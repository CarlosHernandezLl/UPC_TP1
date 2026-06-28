"use client";

import React, { ReactNode, useEffect, useState } from 'react';

export type UserRole = 'ADMIN' | 'SUPERVISOR' | 'GERENTE' | 'AUDITOR';

interface RoleGuardProps {
    children: ReactNode;
    allowedRoles: UserRole[];
    fallback?: ReactNode;
}

export default function RoleGuard({ children, allowedRoles, fallback = null }: RoleGuardProps) {
    const [userRole, setUserRole] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        // Recuperamos el rol del LocalStorage de forma segura al montar el componente
        if (typeof window !== "undefined") {
            const role = localStorage.getItem("scada_userRole");
            setUserRole(role);
            setMounted(true);
        }
    }, []);

    if (!mounted) return null;

    const hasAccess = userRole && (allowedRoles.includes(userRole as UserRole) || userRole === 'ADMIN');

    if (!hasAccess) {
        return <>{fallback}</>;
    }

    return <>{children}</>;
}