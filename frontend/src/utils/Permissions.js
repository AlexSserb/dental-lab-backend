
export function isDirector(user) {
    return user?.group_id === 1;
}

export function isLabAdmin(user) {
    return user?.group_id === 2;
}

export function isChiefTech(user) {
    return user?.group_id === 3;
}

export function isPhysician(user) {
    return !user.group_id;
}
