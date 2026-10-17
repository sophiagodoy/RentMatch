import * as jsonwebtoken from 'jsonwebtoken';

const jwt = (jsonwebtoken as any).default || jsonwebtoken;

const jwt_secret = process.env.JWT_SECRET
const jwt_expires = process.env.JWT_EXPIRES

export function generateToken(id: string) {
    if (!jwt_secret || !jwt_expires) throw new Error("variaveis jwt nulas")
    const token = jwt.sign({id}, jwt_secret, {
        expiresIn: parseInt(jwt_expires)
    })
    return token
}

export function verifyToken(token: string) {
    if (!jwt_secret) throw new Error("variaveis jwt nulas")
    const data = jwt.verify(token, jwt_secret)
    return data;
}