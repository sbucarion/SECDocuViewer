import logo from './logo.svg';
import './App.css';
import { Routes, Route, HashRouter } from "react-router-dom";
import Home from './pages/Home'

function App() {
  return (
    <div className="App">
      <HashRouter>
        <Routes>
          {/* Home is for landing page of unauth users */}
          <Route path="/" element={<Home />} />
        </Routes>
      </HashRouter>
    </div>
  );
}


export default App;