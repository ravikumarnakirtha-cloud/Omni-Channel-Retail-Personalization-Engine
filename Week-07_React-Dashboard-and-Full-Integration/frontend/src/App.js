import React, { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend, ResponsiveContainer } from "recharts";
import axios from "axios";

const API = "/api";
const COLORS = ["#1F4E79","#2E75B6","#E67E22","#1E7E34"];

const card = { background:"#fff", borderRadius:8, padding:20, boxShadow:"0 2px 8px rgba(0,0,0,0.1)", marginBottom:20 };
const badge = (color) => ({ background:color, color:"#fff", borderRadius:4, padding:"2px 10px", fontSize:12, fontWeight:600 });

function StatCard({ label, value, color="#1F4E79" }) {
  return (
    <div style={{ ...card, textAlign:"center", flex:1, margin:8 }}>
      <div style={{ fontSize:32, fontWeight:700, color }}>{value}</div>
      <div style={{ fontSize:14, color:"#666", marginTop:4 }}>{label}</div>
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState(null);
  const [segments, setSegments] = useState(null);
  const [summary, setSummary] = useState(null);
  const [gateway, setGateway] = useState(null);
  const [notifResult, setNotifResult] = useState(null);
  const [notifSeg, setNotifSeg] = useState("high_value");
  const [notifCh, setNotifCh] = useState("email");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      axios.get(`${API}/health`).catch(()=>null),
      axios.get(`${API}/analytics/segments`).catch(()=>null),
      axios.get(`${API}/analytics/summary`).catch(()=>null),
      axios.get(`${API}/gateway/stats`).catch(()=>null),
    ]).then(([h,s,sum,g]) => {
      setHealth(h?.data);
      setSegments(s?.data);
      setSummary(sum?.data);
      setGateway(g?.data);
      setLoading(false);
    }).catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const sendNotif = () => {
    axios.post(`${API}/notify`, { user_id:"dashboard-test", segment:notifSeg, channel:notifCh })
      .then(r => setNotifResult(r.data))
      .catch(e => setNotifResult({ error: e.message }));
  };

  const pieData = segments ? Object.entries(segments.distribution||{}).map(([name,value])=>({name,value})) : [];
  const barData = summary ? summary.map(s=>({ name:s.segment, Revenue:Math.round(s.total_revenue), AvgSpend:Math.round(s.avg_monetary) })) : [];

  if (loading) return <div style={{ display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",fontFamily:"Arial",fontSize:20,color:"#1F4E79" }}>Loading dashboard...</div>;
  if (error) return <div style={{ padding:40,fontFamily:"Arial",color:"red" }}>Error: {error}</div>;

  return (
    <div style={{ fontFamily:"Arial,sans-serif", background:"#f0f4f8", minHeight:"100vh", padding:24 }}>

      {/* Header */}
      <div style={{ background:"linear-gradient(135deg,#1F4E79,#2E75B6)", borderRadius:10, padding:"20px 28px", marginBottom:24, color:"#fff" }}>
        <h1 style={{ margin:0, fontSize:24 }}>Omni-Channel Retail Personalization Engine</h1>
        <div style={{ fontSize:13, marginTop:6, opacity:0.85 }}>React Dashboard — Week 07 | Full Integration</div>
        {health && (
          <div style={{ marginTop:12, display:"flex", gap:12 }}>
            {Object.entries(health.services||{}).map(([svc,status])=>(
              <span key={svc} style={badge(status==="healthy"?"#1E7E34":"#C0392B")}>{svc}: {status}</span>
            ))}
          </div>
        )}
      </div>

      {/* Stats row */}
      {segments && (
        <div style={{ display:"flex", flexWrap:"wrap", marginBottom:4 }}>
          <StatCard label="Total Users" value={segments.total} color="#1F4E79" />
          {Object.entries(segments.distribution||{}).map(([seg,cnt],i)=>(
            <StatCard key={seg} label={seg.replace("_"," ")} value={cnt} color={COLORS[i%COLORS.length]} />
          ))}
          {gateway && <StatCard label="Gateway Requests" value={gateway.total_requests} color="#E67E22" />}
        </div>
      )}

      {/* Charts row */}
      <div style={{ display:"flex", gap:20, flexWrap:"wrap", marginBottom:20 }}>

        {/* Pie chart */}
        <div style={{ ...card, flex:1, minWidth:280 }}>
          <h3 style={{ margin:"0 0 16px", color:"#1F4E79" }}>Customer Segment Distribution</h3>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>
                {pieData.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar chart */}
        <div style={{ ...card, flex:2, minWidth:360 }}>
          <h3 style={{ margin:"0 0 16px", color:"#1F4E79" }}>Revenue & Avg Spend by Segment</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} margin={{ top:5,right:20,left:0,bottom:5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:11 }} />
              <Tooltip formatter={v=>`$${v.toLocaleString()}`} />
              <Legend />
              <Bar dataKey="Revenue" fill="#1F4E79" />
              <Bar dataKey="AvgSpend" fill="#2E75B6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* RFM table */}
      {summary && (
        <div style={{ ...card, marginBottom:20 }}>
          <h3 style={{ margin:"0 0 16px", color:"#1F4E79" }}>Segment RFM Summary</h3>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:14 }}>
            <thead>
              <tr style={{ background:"#1F4E79", color:"#fff" }}>
                {["Segment","Count","Avg Recency (days)","Avg Frequency","Avg Spend ($)","Total Revenue ($)"].map(h=>(
                  <th key={h} style={{ padding:"8px 12px", textAlign:"left" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {summary.map((s,i)=>(
                <tr key={s.segment} style={{ background:i%2===0?"#f8f9fa":"#fff" }}>
                  <td style={{ padding:"8px 12px", fontWeight:600, color:"#1F4E79" }}>{s.segment}</td>
                  <td style={{ padding:"8px 12px" }}>{s.count}</td>
                  <td style={{ padding:"8px 12px" }}>{s.avg_recency}</td>
                  <td style={{ padding:"8px 12px" }}>{s.avg_frequency}</td>
                  <td style={{ padding:"8px 12px" }}>${s.avg_monetary?.toLocaleString()}</td>
                  <td style={{ padding:"8px 12px" }}>${s.total_revenue?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Send notification */}
      <div style={{ ...card }}>
        <h3 style={{ margin:"0 0 16px", color:"#1F4E79" }}>Send Test Notification</h3>
        <div style={{ display:"flex", gap:12, alignItems:"center", flexWrap:"wrap" }}>
          <select value={notifSeg} onChange={e=>setNotifSeg(e.target.value)} style={{ padding:"8px 12px", borderRadius:4, border:"1px solid #ccc" }}>
            {["high_value","frequent_buyer","at_risk","new_customer"].map(s=><option key={s} value={s}>{s}</option>)}
          </select>
          <select value={notifCh} onChange={e=>setNotifCh(e.target.value)} style={{ padding:"8px 12px", borderRadius:4, border:"1px solid #ccc" }}>
            {["email","sms","push"].map(c=><option key={c} value={c}>{c}</option>)}
          </select>
          <button onClick={sendNotif} style={{ padding:"8px 20px", background:"#1F4E79", color:"#fff", border:"none", borderRadius:4, cursor:"pointer", fontWeight:600 }}>
            Send Offer
          </button>
          {notifResult && (
            <span style={{ fontSize:13, color: notifResult.error?"red":"#1E7E34", fontWeight:600 }}>
              {notifResult.error ? `Error: ${notifResult.error}` : `Sent! ${notifResult.offer_type} — ${notifResult.discount_pct}% off via ${notifResult.channel}`}
            </span>
          )}
        </div>
      </div>

      {/* Gateway recent requests */}
      {gateway?.recent_requests && (
        <div style={{ ...card }}>
          <h3 style={{ margin:"0 0 12px", color:"#1F4E79" }}>Gateway Recent Requests</h3>
          <table style={{ width:"100%", borderCollapse:"collapse", fontSize:13 }}>
            <thead>
              <tr style={{ background:"#2E75B6", color:"#fff" }}>
                {["Method","Path","Timestamp"].map(h=><th key={h} style={{ padding:"6px 10px", textAlign:"left" }}>{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {gateway.recent_requests.slice(-8).reverse().map((r,i)=>(
                <tr key={i} style={{ background:i%2===0?"#f8f9fa":"#fff" }}>
                  <td style={{ padding:"6px 10px", fontWeight:600, color:r.method==="POST"?"#E67E22":"#1F4E79" }}>{r.method}</td>
                  <td style={{ padding:"6px 10px", fontFamily:"monospace" }}>{r.path}</td>
                  <td style={{ padding:"6px 10px", color:"#666" }}>{new Date(r.ts).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={{ textAlign:"center", fontSize:12, color:"#999", marginTop:8 }}>
        Omni-Channel Retail Personalization Engine — Week 07 React Dashboard
      </div>
    </div>
  );
}
