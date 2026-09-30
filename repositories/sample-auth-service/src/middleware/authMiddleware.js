const { verifyToken } = require('../services/authService');
const userModel = require('../models/userModel');

function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or malformed Authorization Bearer token' });
    }

    const token = authHeader.split(' ')[1];
    try {
        const decoded = verifyToken(token);
        const user = userModel.findById(decoded.sub);
        if (!user) {
            return res.status(401).json({ error: 'User associated with token no longer exists' });
        }
        req.user = user;
        next();
    } catch (err) {
        return res.status(403).json({ error: 'Invalid or expired token', message: err.message });
    }
}

module.exports = {
    authenticateToken
};
