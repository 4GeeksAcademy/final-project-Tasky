import React, { createContext, useContext, useMemo, useState, useEffect } from "react";

const UserContext = createContext(null);

export function UserProvider({ children, demo = true, demoUser = { id: 99, role: "tasker" } }) {
    const [user, setUser] = useState(null);

    useEffect(() => {
        if (demo) {
            // Mock: finge que hay un tasker logueado
            setUser(demoUser);
        } else {
            // Cuando usemos auth real: fetch('/api/me').then(r => r.json()).then(setUser)
        }
    }, [demo, demoUser]);

    const value = useMemo(() => ({ user, setUser }), [user]);
    return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
    return useContext(UserContext);
}
