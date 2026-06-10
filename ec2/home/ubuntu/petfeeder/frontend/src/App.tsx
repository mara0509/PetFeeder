import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Line, Bar } from 'react-chartjs-2';
import 'chart.js/auto';
import { Bone, Clock, AlertTriangle, Activity, Wifi } from 'lucide-react';
import './App.css';



//EC2 PUBLIC IP
const API_BASE_URL = //

export default function App() {
//here is stored everything from api/data in data,setdata
//when new information is sent it is stored in data
  const [data, setData] = useState<any>(null);
//here we store the time that is selected by the user
  const [newTime, setNewTime] = useState('');

//AI API use states
const [petData, setPetData] = useState({ type: 'cat', breed: '', age: '', weight: '' });
const [aiAdvice, setAiAdvice] = useState<any>(null);
const [isAiLoading, setIsAiLoading] = useState(false);
const simulatedFoodConsumedToday = 40;
const isEditingProfile = useRef(false);
const [foodConsumedToday, setFoodConsumedToday] = useState(0);

  // Fetch data smoothly in the background&& connects to Flask backend
  const fetchData = async () => {
    try {
//this response will become GET API_BASE_URL/api/data
//this is the moment when the endpoint created in flask is called and it will respond with informatio >
      const response = await axios.get(`${API_BASE_URL}/data`);
      setData(response.data);

//if firebase has a saved pet profile
      if (response.data.pet_profile && !aiAdvice && !isEditingProfile.current) {
        setAiAdvice(response.data.pet_profile);
      }

    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  //automatic refresh of the page
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
//every 5 seconds the frontend asks the backend for new information, new data
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
//this awaut axois function sends POST /api/dispense to the backend
    await axios.post(`${API_BASE_URL}/schedule`, { feed_time: newTime });
    setNewTime('');
    fetchData();
  };


// AI API
const fetchAiAdvice = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAiLoading(true);
    try {
      const response = await axios.post(`http://44.222.243.152:5000/api/ai-consultant`, {
        pet_type: petData.type,
        breed: petData.breed,
        age: petData.age,
        weight: petData.weight
      });
      setAiAdvice(response.data);
      isEditingProfile.current = false;
    } catch (error) {
      console.error("AI API failed", error);
    }
    setIsAiLoading(false);
  };
useEffect(() => {
    if (data && data.history && Array.isArray(data.history)) {
      let totalConsumed = 0;
      let previousWeight = null;

      // Get today's date in YYYY-MM-DD format to filter the history
      const todayStr = new Date().toISOString().split('T')[0];

      data.history.forEach((record: any) => {
        // Only count records from today
        if (record.timestamp && record.timestamp.includes(todayStr)) {
          // If your history stores percentage, multiply it by your bowl capacity to get grams here!
          // Assuming record.food_percentage is what you get from Firebase
          const currentWeight = record.food_percentage;

          // If the weight dropped since the last reading, the pet ate!
          if (previousWeight !== null && currentWeight < previousWeight) {
            totalConsumed += (previousWeight - currentWeight);
          }
          previousWeight = currentWeight;
        }
      });

      setFoodConsumedToday(totalConsumed);
    }
  }, [data]); // This recalculates every time new data arrives from Flask

  if (!data) return <div className="loading">Loading Smart Feeder Data...</div>;

  const { live, schedule, history, charts } = data;
//styling for form input
const inputStyle = {
    backgroundColor: '#f8f9fa', // Very light, clean grey
    color: '#333',              // Dark grey text so it is easy to read
    border: '1px solid #e0e0e0',
    padding: '12px',            // Makes the boxes taller and easier to tap on a phone
    borderRadius: '8px',
    fontSize: '1rem'
  };

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

          {/* --- AI Nutrition Consultant Card --- */}
          <div className="card">
            <h2>🧠 AI Nutrition Consultant</h2>

            {!aiAdvice ? (
              <form onSubmit={fetchAiAdvice} style={{ display: 'flex', flexDirection: 'column', gap: '>
                <input type="text" style={inputStyle} placeholder="Pet Type (e.g., Cat or Dog)" requir>
                <input type="text" style={inputStyle} placeholder="Breed (e.g., Siamese)" required onC>
                <input type="number" style={inputStyle} placeholder="Age (years)" required onChange={e>
                <input type="number" style={inputStyle} placeholder="Weight (kg)" required step="0.1" >

                <button type="submit" className="btn btn-primary" disabled={isAiLoading}>
                  {isAiLoading ? "Consulting AI..." : "Get Diet Plan"}
                </button>
              </form>
            ) : (
              <div>
                <p><strong>Target:</strong> {aiAdvice.recommended_grams_per_day}g per day ({aiAdvice.n>
                <p style={{ fontSize: '0.9rem', color: '#666' }}><em>{aiAdvice.health_warning}</em></p>

                {/* OVEREATING WARNING LOGIC */}
                {foodConsumedToday > aiAdvice.recommended_grams_per_day && (
                  <div className="alert-box" style={{ backgroundColor: '#ffebee', color: '#c62828', bo>
                    <h3 style={{ margin: '0 0 5px 0' }}>⚠️ Overeating Alert</h3>
                    <p style={{ margin: 0 }}>Your pet has consumed {Math.round(foodConsumedToday)}g to>
                  </div>
                )}

                <button onClick={() => {setAiAdvice(null); isEditingProfile.current=true;}} className=>
              </div>
            )}
</div>
        </section>

        {/* RIGHT COLUMN: Analytics */}
        <section className="col">

          {/* Today's Consumption Card */}
          <div className="card">
            <h2>🍽️ Today's Consumption</h2>
            <div
              className="big-stat"
              style={{ color: aiAdvice && foodConsumedToday > aiAdvice.recommended_grams_per_day ? '#d>
            >
              {Math.round(foodConsumedToday)}<span>g</span>
            </div>
            {aiAdvice ? (
              <p>Daily Target: {aiAdvice.recommended_grams_per_day}g</p>
            ) : (
              <p>Consult AI to set a target limit!</p>
            )}
          </div>

          <div className="card">
            <h2>Inventory Over Time</h2>
            <Line
              data={{
                labels: charts.inventory.labels,
                datasets: [{ label: 'Food Level (g)', data: charts.inventory.data.map(value => Math.ro>
              }}
            />
          </div>

          <div className="card">
            <h2>Daily Pet Visits</h2>
            <Bar
              data={{
                labels: charts.visits.labels,
                datasets: [{ label: 'Visits', data: charts.visits.data, backgroundColor: '#aacaef', bo>
              }}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
