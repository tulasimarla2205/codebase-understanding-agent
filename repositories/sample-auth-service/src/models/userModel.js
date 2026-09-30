// In-memory user database simulation for demonstration
const users = new Map();

function findByEmail(email) {
    for (const user of users.values()) {
        if (user.email.toLowerCase() === email.toLowerCase()) {
            return user;
        }
    }
    return null;
}

function findById(id) {
    return users.get(id) || null;
}

function createUser(userData) {
    const id = `usr_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    const user = {
        id,
        email: userData.email,
        passwordHash: userData.passwordHash,
        name: userData.name || '',
        createdAt: new Date().toISOString()
    };
    users.set(id, user);
    return user;
}

module.exports = {
    findByEmail,
    findById,
    createUser
};
