const mongoose = require("mongoose");

const detectionSchema = new mongoose.Schema(
    {
        busId: {
            type: String,
            required: true
        },

        cameraId: {
            type: String,
            required: true
        },

        location: {
            latitude: {
                type: Number,
                required: true
            },

            longitude: {
                type: Number,
                required: true
            }
        },

        detection: {
            type: {
                type: String,
                required: true
            },

            confidence: {
                type: Number,
                required: true
            },

            severity: {
                type: String,
                required: true
            }
        },

        timestamp: {
            type: Date,
            default: Date.now
        }
    },

    {
        timestamps: true
    }
);

module.exports = mongoose.model("Detection", detectionSchema);