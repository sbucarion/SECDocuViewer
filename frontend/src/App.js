import { Routes, Route, HashRouter } from "react-router-dom";
import Home from './pages/Home'
import './index.css'

function App() {
  return (
    //This template to create as many webpages as you want
    //Each Route is a specific webpage and they call 
    //The respective file that has all webpage info
    <div className="App">
      <h1>hello</h1>
      <HashRouter>
        <Routes>
         {/* Home is for landing page of unauth users */}
        <Route path="/" element={<Home/>}/>
      </Routes>
    </HashRouter></div>
  );
}

export default App;
