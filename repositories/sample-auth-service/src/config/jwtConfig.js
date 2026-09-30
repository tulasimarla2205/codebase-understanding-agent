module.exports = {
    jwtSecret: process.env.JWT_SECRET || 'hackathon-default-jwt-secret-key-32chars',
    jwtExpiresIn: process.env.JWT_EXPIRES_IN || '2h',
    saltRounds: 10
};
