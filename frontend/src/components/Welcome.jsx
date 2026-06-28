import React, {useEffect, useState} from "react";
import {Link} from "react-router-dom";

export default function Welcome({user}) {
  // Fecha de inicio del Mundial 2026 (ajusta si es necesario)
  const mundialDate = new Date("2026-06-11T18:00:00Z");
  const [timeLeft, setTimeLeft] = useState({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  });

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const diff = mundialDate - now;
      if (diff > 0) {
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
        const minutes = Math.floor((diff / (1000 * 60)) % 60);
        const seconds = Math.floor((diff / 1000) % 60);
        setTimeLeft({days, hours, minutes, seconds});
      } else {
        setTimeLeft({days: 0, hours: 0, minutes: 0, seconds: 0});
      }
    };
    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-2 sm:px-4 py-6 sm:py-10 bg-gradient-to-br from-green-900 via-slate-900 to-black">
      <div className="flex flex-col md:flex-row items-center gap-6 sm:gap-10 mb-6 sm:mb-8 w-full">
        <img
          src="/img/logo.png"
          alt="Logo"
          className="w-40 sm:w-80 h-auto object-contain drop-shadow-lg rounded-lg p-2 mx-auto"
        />
        <div className="text-center md:text-left w-full">
          <h1 className="text-2xl sm:text-4xl md:text-5xl font-black text-green-400 mb-2 drop-shadow-lg">
            Bienvenido!
            <br />
            {user.username}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-slate-200 mb-4 max-w-xl mx-auto md:mx-0">
            Hay momentos en la vida en los que el camino parece demasiado difícil y las fuerzas parecen no alcanzar.
            Pero aun en medio de la tormenta, nunca dejen de creer que cada amanecer trae una nueva oportunidad.
          </p>
          <div className="flex flex-col md:flex-row gap-3 sm:gap-4 items-center md:items-start justify-center md:justify-start">
            <Link
              to="/partidos"
              className="bg-green-600 hover:bg-green-500 text-white px-8 py-3 rounded-lg font-bold shadow-lg shadow-green-900/20 transition-all transform active:scale-95"
            >
              Mis predicciones
            </Link>
            <Link
              to="/clasificacion"
              className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-lg font-bold shadow-lg shadow-blue-900/20 transition-all transform active:scale-95"
            >
              Clasificación
            </Link>
          </div>
        </div>
      </div>
      <div className="flex flex-col items-center gap-2 mt-6 sm:mt-8">
        <span className="text-slate-400 text-sm mb-2"></span>
        <img
          src="/img/mundial2026.png"
          alt="Logo Mundial 2026"
          className="w-40 sm:w-80 h-40 sm:h-80 object-contain drop-shadow-xl animate-fade-in"
        />
      </div>
      {/* Contador dentro del cuadro degradado, abajo a la derecha */}
      <div className="w-full flex justify-center sm:justify-end items-end">
        <div className="mb-2 mr-0 sm:mr-2 bg-slate-900/90 border border-green-700 rounded-xl px-4 sm:px-6 py-3 sm:py-4 shadow-2xl flex flex-col items-center animate-fade-in text-sm sm:text-base">
          <span className="text-green-400 font-bold text-lg mb-1">
            Días para el inicio:
          </span>
          <span className="text-2xl font-black text-white tracking-widest">
            {timeLeft.days}d {timeLeft.hours}h {timeLeft.minutes}m{" "}
            {timeLeft.seconds}s
          </span>
        </div>
      </div>
    </div>
  );
}
