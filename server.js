require("dotenv").config();

const express = require("express");
const cors = require("cors");
const mongoose = require("mongoose");
const Detection = require("./models/Detection");

const app = express();

app.use(cors());
app.use(express.json());

// Temporary storage
const detections = [];

// Configuration
const PORT = 5000;
const CONFIRMATION_RADIUS_METERS = 30;
const MIN_BUSES_REQUIRED = 2;

// Home route
app.get("/", (req, res) => {
    res.json({
        project: "CitySense",
        message: "CitySense Backend is running successfully!",
        status: "success"
    });
});

// Health check
app.get("/api/health", (req, res) => {
    res.json({
        project: "CitySense",
        server: "healthy",
        timestamp: new Date().toISOString()
    });
});

// Calculate distance between two GPS coordinates
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000;

    const toRadians = (degrees) => {
        return degrees * Math.PI / 180;
    };

    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);

    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(toRadians(lat1)) *
        Math.cos(toRadians(lat2)) *
        Math.sin(dLon / 2) ** 2;

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c;
}

// Validate detection data
function validateDetection(data) {
    if (!data.busId || !data.cameraId) {
        return "busId and cameraId are required";
    }

    if (!data.location ||
        typeof data.location.latitude !== "number" ||
        typeof data.location.longitude !== "number") {
        return "Valid location with latitude and longitude is required";
    }

    if (!data.detection ||
        data.detection.type !== "pothole" ||
        typeof data.detection.confidence !== "number" ||
        !data.detection.severity) {
        return "Valid pothole detection data is required";
    }

    if (
        data.detection.confidence < 0 ||
        data.detection.confidence > 1
    ) {
        return "Confidence must be between 0 and 1";
    }

    return null;
}

// POST: Receive AI detection
app.post("/api/detections", (req, res) => {
    const data = req.body;

    const validationError = validateDetection(data);

    if (validationError) {
        return res.status(400).json({
            success: false,
            message: validationError
        });
    }

    // Prevent duplicate detection from the same bus
    // at the same location within 30 seconds
    const isDuplicate = detections.some(existing => {
        const distance = calculateDistance(
            existing.location.latitude,
            existing.location.longitude,
            data.location.latitude,
            data.location.longitude
        );

        const timeDifference =
            Math.abs(
                new Date(existing.timestamp).getTime() -
                new Date(data.timestamp || Date.now()).getTime()
            );

        return (
            existing.busId === data.busId &&
            distance <= CONFIRMATION_RADIUS_METERS &&
            timeDifference <= 30000
        );
    });

    if (isDuplicate) {
        return res.status(409).json({
            success: false,
            message: "Duplicate detection from this bus"
        });
    }

    const detection = {
        id: `DET-${detections.length + 1}`,
        ...data,
        receivedAt: new Date().toISOString()
    };

    detections.push(detection);

    res.status(201).json({
        success: true,
        message: "AI detection received successfully",
        detection
    });
});

// GET: Retrieve all detections
app.get("/api/detections", (req, res) => {
    res.json({
        success: true,
        count: detections.length,
        detections
    });
});

// GET: Multi-bus confirmed potholes
app.get("/api/confirmed-potholes", (req, res) => {
    const potholes = detections.filter(
        d => d.detection.type === "pothole"
    );

    const groups = [];

    potholes.forEach(detection => {
        let matchingGroup = null;

        for (const group of groups) {
            const distance = calculateDistance(
                group.latitude,
                group.longitude,
                detection.location.latitude,
                detection.location.longitude
            );

            if (distance <= CONFIRMATION_RADIUS_METERS) {
                matchingGroup = group;
                break;
            }
        }

        if (matchingGroup) {
            matchingGroup.detections.push(detection);

            // Update average location
            const count = matchingGroup.detections.length;

            matchingGroup.latitude =
                matchingGroup.detections.reduce(
                    (sum, d) => sum + d.location.latitude, 0
                ) / count;

            matchingGroup.longitude =
                matchingGroup.detections.reduce(
                    (sum, d) => sum + d.location.longitude, 0
                ) / count;

        } else {
            groups.push({
                latitude: detection.location.latitude,
                longitude: detection.location.longitude,
                detections: [detection]
            });
        }
    });

    const confirmedPotholes = groups.map((group, index) => {
        const uniqueBuses = [
            ...new Set(group.detections.map(d => d.busId))
        ];

        const severityRank = {
            low: 1,
            medium: 2,
            high: 3,
            critical: 4
        };

        const severity = group.detections.reduce((highest, detection) => {
            const currentSeverity = detection.detection.severity;
            return severityRank[currentSeverity.toLowerCase()] > severityRank[highest.toLowerCase()]
                ? currentSeverity
                : highest;
        }, group.detections[0].detection.severity);

        const averageConfidence =
            group.detections.reduce(
                (sum, d) => sum + d.detection.confidence,
                0
            ) / group.detections.length;

        const isConfirmed =
            uniqueBuses.length >= MIN_BUSES_REQUIRED;

        return {
            potholeId: `POTHOLE-${index + 1}`,
            location: {
                latitude: group.latitude,
                longitude: group.longitude
            },
            busesDetected: uniqueBuses,
            totalDetections: group.detections.length,
            uniqueBusCount: uniqueBuses.length,
            confirmationPercentage: Number(
                Math.min((uniqueBuses.length / MIN_BUSES_REQUIRED) * 100, 100).toFixed(2)
            ),
            averageConfidence: Number(
                averageConfidence.toFixed(2)
            ),
            severity,
            status: isConfirmed ? "CONFIRMED" : "UNVERIFIED",
            verification: isConfirmed
                ? "Multiple buses detected this pothole"
                : "Waiting for confirmation from another bus"
        };
    });

    res.json({
        success: true,
        count: confirmedPotholes.length,
        confirmedPotholes
    });
});

// Connect to MongoDB and start server
mongoose.connect(process.env.MONGO_URI)
    .then(() => {
        console.log("✅ MongoDB connected successfully!");

        app.listen(PORT, () => {
            console.log(
                `🚀 CitySense Backend running on port ${PORT}`
            );
        });
    })
    .catch((error) => {
        console.error("❌ MongoDB connection failed:", error.message);
    });