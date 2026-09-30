const authService = require('../services/authService');

async function handleRegister(req, res) {
    try {
        const { email, password, name } = req.body;
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }
        const result = await authService.register(email, password, name);
        return res.status(201).json(result);
    } catch (err) {
        return res.status(400).json({ error: err.message });
    }
}

async function handleLogin(req, res) {
    try {
        const { email, password } = req.body;
        if (!email || !password) {
            return res.status(400).json({ error: 'Email and password are required' });
        }
        const result = await authService.login(email, password);
        return res.status(200).json(result);
    } catch (err) {
        return res.status(401).json({ error: err.message });
    }
}

function handleProfile(req, res) {
    return res.status(200).json({
        user: {
            id: req.user.id,
            email: req.user.email,
            name: req.user.name,
            createdAt: req.user.createdAt
        }
    });
}

module.exports = {
    handleRegister,
    handleLogin,
    handleProfile
};
