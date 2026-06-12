import React, {useState, useEffect} from "react";
import {getLeaderboard} from "../api";

function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, []);

  const loadLeaderboard = async () => {
    try {
      const response = await getLeaderboard();
      setLeaderboard(Array.isArray(response.data) ? response.data : []);
      setLoading(false);
    } catch (err) {
      console.error("Error loading leaderboard:", err);
      setLoading(false);
    }
  };

  const getMedalEmoji = (position) => {
    if (position === 0) return "🥇";
    if (position === 1) return "🥈";
    if (position === 2) return "🥉";
    return "";
  };

  if (loading) {
    return <div className="text-center py-10">Cargando...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl sm:text-3xl font-black mb-6 sm:mb-8 text-white text-center">
        🏆 Tabla de Clasificación
      </h1>

      <div className="bg-slate-800 rounded-xl shadow-xl border border-slate-700 overflow-hidden">
        {leaderboard.length === 0 ? (
          <div className="text-center text-slate-500 py-10">
            No hay datos disponibles en la tabla de clasificación
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[600px] text-sm sm:text-base">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="text-left py-4 px-6 text-slate-400 font-bold text-sm uppercase tracking-wider">
                    #
                  </th>
                  <th className="text-left py-4 px-6 text-slate-400 font-bold text-sm uppercase tracking-wider">
                    Nombre del Jugador
                  </th>
                  <th className="text-left py-4 px-6 text-slate-400 font-bold text-sm uppercase tracking-wider">
                    Empresa
                  </th>
                  <th className="text-center py-4 px-6 text-slate-400 font-bold text-sm uppercase tracking-wider">
                    Puntos
                  </th>
                  <th className="text-center py-4 px-6 text-slate-400 font-bold text-sm uppercase tracking-wider">
                    Campeón
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {leaderboard.map((entry, index) => (
                  <tr
                    key={index}
                    className={`hover:bg-slate-700/50 transition-colors ${
                      index < 3 ? "bg-slate-700/20" : ""
                    }`}
                  >
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-bold text-lg ${index === 0 ? "text-yellow-400" : index === 1 ? "text-slate-300" : index === 2 ? "text-amber-600" : "text-slate-500"}`}
                        >
                          {index + 1}
                        </span>
                        {getMedalEmoji(index) && (
                          <span className="text-2xl">
                            {getMedalEmoji(index)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`font-bold text-white ${index < 3 ? "text-lg" : ""}`}
                      >
                        {entry.username}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <span className="text-slate-300 font-medium">
                        {entry.empresa || "-"}
                      </span>
                    </td>
                    {/* Puntos */}
                    <td className="text-center py-4 px-6">
                      <span className="text-2xl font-black text-green-400">
                        {entry.total_points}
                      </span>
                    </td>
                    <td className="text-center py-4 px-6">
                      <span className="font-bold text-yellow-300">
                        {entry.champion ? (
                          <>
                            <span className="text-2xl mr-1">👑</span>
                            {entry.champion}
                          </>
                        ) : (
                          <span className="text-slate-500 italic">-</span>
                        )}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="mt-8 bg-slate-800/50 p-4 sm:p-6 rounded-xl border border-slate-700 text-sm sm:text-base">
        <h3 className="font-bold mb-3 text-white text-lg">
          🏆 Sistema de Puntuación Oficial
        </h3>
        <div className="space-y-4 text-slate-300">
          <div>
            <span className="font-bold text-white">⚽ Fase de Grupos</span>
            <ul className="list-disc ml-6">
              <li>5 puntos por un marcador exacto.</li>
              <li>
                3 puntos por predecir el ganador o un empate (sin coincidir con el marcador exacto).
              </li>
              <li>
                1 punto por predecir solo uno de los goles en el marcador (resultado parcial).
              </li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">
              🔥 32vos
            </span>
            <ul className="list-disc ml-6">
              <li>6 puntos por un marcador exacto.</li>
              <li>3 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">🔥 Octavos de Final</span>
            <ul className="list-disc ml-6">
              <li>7 puntos por un marcador exacto.</li>
              <li>4 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">🔥 Cuartos de Final</span>
            <ul className="list-disc ml-6">
              <li>9 puntos por un marcador exacto.</li>
              <li>5 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">🔥 Semifinales</span>
            <ul className="list-disc ml-6">
              <li>12 puntos por un marcador exacto.</li>
              <li>6 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">🥉 Tercer Lugar</span>
            <ul className="list-disc ml-6">
              <li>10 puntos por un marcador exacto.</li>
              <li>5 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">🏆 Final</span>
            <ul className="list-disc ml-6">
              <li>15 puntos por un marcador exacto.</li>
              <li>8 puntos por predecir el ganador o un empate.</li>
            </ul>
          </div>
          <div>
            <span className="font-bold text-white">👑 Campeón Mundial</span>
            <ul className="list-disc ml-6">
              <li>15 puntos adicionales por predecir el campeón del torneo.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Leaderboard;
