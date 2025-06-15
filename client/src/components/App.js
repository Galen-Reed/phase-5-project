import React, { useEffect, useState } from "react";
import { Routes, Route } from "react-router-dom";
import Login from "../Pages/Login";
import NavBar from "../components/NavBar";

function App() {

  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetch("/check_session", {
      method: "GET",
      credentials: "same-origin",
    }).then((r) => {
      if (r.ok) {
        r.json().then((userData) => {
          setUser(userData);
      });
      }
    });
  }, []);

  if (!user) return <Login onLogin={handleLogin} />

  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" />

      </Routes>
    </>
  )
}

export default App;
