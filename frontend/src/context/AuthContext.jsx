import React, { createContext, useContext, useState, useEffect } from 'react';
import { decodeJwt } from '../utils/jwt';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [jwtToken, setJwtToken] = useState(() => localStorage.getItem("jwt_token") || "");
  const [user, setUser] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const logout = () => {
    localStorage.removeItem("jwt_token");
    setJwtToken("");
    setUser(null);
  };

  useEffect(() => {
    if (jwtToken) {
      const claims = decodeJwt(jwtToken);
      if (claims) {
        if (claims.exp && claims.exp * 1000 < Date.now()) {
          logout();
        } else {
          setUser({
            username: claims.username || claims.sub || 'User',
            role: claims.role || 'user'
          });
        }
      } else {
        setUser(null);
      }
    } else {
      setUser(null);
    }
  }, [jwtToken]);

  const loginToken = (token) => {
    localStorage.setItem("jwt_token", token);
    setJwtToken(token);
  };

  return (
    <AuthContext.Provider
      value={{
        jwtToken,
        user,
        isModalOpen,
        setIsModalOpen,
        loginToken,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
