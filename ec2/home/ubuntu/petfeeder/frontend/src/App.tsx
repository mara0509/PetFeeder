import { useEffect, useState } from 'react';
import axios from 'axios';
import { Line, Bar } from 'react-chartjs-2';
import 'chart.js/auto';
import { Bone, Clock, AlertTriangle, Activity, Wifi } from 'lucide-react';
import './App.css';

// --- CONFIGURATION ---
// REPLACE THIS WITH YOUR EC2 PUBLIC IP
const API_BASE_URL = 'http://44.222.243.152:5000/api'; 

export default function App() {
  const [data, setData] = useState<any>(null);
  const [newTime, setNewTime] = useState('');

  // Fetch data smoothly in the background
  const fetchData = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/data`);
      setData(response.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  // Run immediately, then every 5 seconds without reloading the page
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // API Call to Dispense Food
  const handleDispense = async () => {
    await axios.post(`${API_BASE_URL}/dispense`);
    alert("Command sent! Food is dispensing.");
    fetchData(); // Instantly update UI
  };

  // API Call to Add Schedule
  const handleAddSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    await axios.post(`${API_BASE_URL}/schedule`, { feed_time: newTime });
    setNewTime('');
    fetchData();
  };

  if (!data) return <div className="loading">Loading Smart Feeder Data...</div>;

  const { live, schedule, history, charts } = data;

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1><Bone className="icon" /> Smart Pet Feeder</h1>
        <div className="status-badge"><Wifi size={16} /> System Online</div>
      </header>

      <main className="grid">
        {/* LEFT COLUMN: Controls */}
        <section className="col">
          
          {/* Alerts */}
          {live.food_percentage < 5.0 && (
            <div className="alert danger">
              <AlertTriangle size={20} /> WARNING: Food critically low ({live.food_percentage}%)
            </div>
          )}
          {live.pet_detected && (
            <div className="alert warning">
              <h3>🐈 Pet is waiting!</h3>
              <button onClick={handleDispense} className="btn btn-blue">Approve Feeding</button>
            </div>
          )}

          {/* Live Status Card */}
          <div className="card">
            <h2>Live Status</h2>
            <div className="big-stat">
              {Math.round(live.food_percentage )}<span>g</span>
            </div>
            <p>Food Remaining in Hopper</p>
          </div>

          {/* Manual Control */}
          <div className="card">
            <h2>Manual Control</h2>
            <button onClick={handleDispense} className="btn btn-primary">
              <Activity size={18} /> Dispense Food Now
            </button>
          </div>

          {/* Schedule */}
          <div className="card">
            <h2><Clock size={18} /> Scheduled Feedings</h2>
            <form onSubmit={handleAddSchedule} className="schedule-form">
              <input 
                type="time" 
                value={newTime} 
                onChange={(e) => setNewTime(e.target.value)} 
                required 
              />
              <button type="submit" className="btn btn-secondary">Add</button>
            </form>
            <ul className="schedule-list">
              {schedule.length > 0 ? schedule.map((time: string, i: number) => (
                <li key={i}>{time}</li>
              )) : <li>No schedules set.</li>}
            </ul>
          </div>
        </section>

        {/* RIGHT COLUMN: Analytics */}
        <section className="col">
          <div className="card">
            <h2>Inventory Over Time</h2>
            <Line 
              data={{
                labels: charts.inventory.labels,
                datasets: [{ label: 'Food Level (g)', data: charts.inventory.data.map(value => Math.round(value)), borderColor: '#d65b7e', backgroundColor: 'rgba(214, 91, 126, 0.2)', fill: true, tension: 0.4 }]
              }} 
            />
          </div>

          <div className="card">
            <h2>Daily Pet Visits</h2>
            <Bar 
              data={{
                labels: charts.visits.labels,
                datasets: [{ label: 'Visits', data: charts.visits.data, backgroundColor: '#aacaef', borderRadius: 6 }]
              }} 
            />
          </div>
        </section>
      </main>
    </div>
  );
}
