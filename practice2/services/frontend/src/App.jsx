import React, { useState, useEffect } from 'react';

function App() {
    const [stats, setStats] = useState({ total_users: 0, total_subscriptions: 0 });
    const [status, setStatus] = useState("Loading...");

    useEffect(() => {
        // Делаем GET-запрос к нашему API Gateway
        fetch('http://localhost:8000/api/v1/stats')
        .then(res => {
            if (!res.ok) throw new Error("API Network response was not ok");
            return res.json();
        })
        .then(data => {
            setStats(data);
            setStatus("Online");
        })
        .catch((err) => {
            console.error(err);
            setStatus("Offline / Error");
        });
    }, []);

    return (
        <div className="p-8 max-w-4xl mx-auto mt-10">
        <h1 className="text-3xl font-bold mb-8 text-gray-800 border-b pb-4">
            MOEX Price Alert - Admin Dashboard
        </h1>
        
        <div className="grid grid-cols-2 gap-6 mb-8">
            <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500 transform transition hover:scale-105">
            <h2 className="text-sm text-gray-400 uppercase font-bold tracking-wider">Всего пользователей</h2>
            <p className="text-4xl font-black text-gray-800 mt-2">{stats.total_users}</p>
            </div>
            
            <div className="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500 transform transition hover:scale-105">
            <h2 className="text-sm text-gray-400 uppercase font-bold tracking-wider">Активные подписки</h2>
            <p className="text-4xl font-black text-gray-800 mt-2">{stats.total_subscriptions}</p>
            </div>
        </div>

        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 inline-block">
            <span className="font-bold text-gray-600 mr-2">Статус API: </span>
            <span className={status === "Online" ? "text-green-500 font-black animate-pulse" : "text-red-500 font-black"}>
            ● {status}
            </span>
        </div>
        </div>
    );
}

export default App;