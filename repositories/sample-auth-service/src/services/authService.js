const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { jwtSecret, jwtExpiresIn, saltRounds } = require('../config/jwtConfig');
const userModel = require('../models/userModel');

async function register(email, password, name) {
    const existing = userModel.findByEmail(email);
    if (existing) {
        throw new Error('User already exists with this email');
    }

    const passwordHash = await bcrypt.hash(password, saltRounds);
    const user = userModel.createUser({ email, passwordHash, name });

    const token = generateToken(user);
    return {
        user: { id: user.id, email: user.email, name: user.name },
        token
    };
}

async function login(email, password) {
    const user = userModel.findByEmail(email);
    if (!user) {
        throw new Error('Invalid email or password');
    }

    const isValid = await bcrypt.compare(password, user.passwordHash);
    if (!isValid) {
        throw new Error('Invalid email or password');
    }

    const token = generateToken(user);
    return {
        user: { id: user.id, email: user.email, name: user.name },
        token
    };
}

function generateToken(user) {
    const payload = {
        sub: user.id,
        email: user.email,
        name: user.name
    };
    return jwt.sign(payload, jwtSecret, { expiresIn: jwtExpiresIn });
}

function verifyToken(token) {
    return jwt.verify(token, jwtSecret);
}

module.exports = {
    register,
    login,
    generateToken,
    verifyToken
};
