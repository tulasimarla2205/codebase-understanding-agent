const express = require('express');
const dotenv = require('dotenv');
const authRoutes = require('./routes/authRoutes');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 4000;

app.use(express.json());

// Healthcheck endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'sample-auth-service' });
});

// Authentication routes
app.use('/api/auth', authRoutes);

if (process.env.NODE_ENV !== 'test') {
    app.listen(PORT, () => {
        console.log(`Auth service running on port ${PORT}`);
    });
}

module.exports = app;
