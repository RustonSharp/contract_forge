import "./index.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

import Header from "./components/Header";
import Home from "./pages/HomePage";
import About from "./pages/AboutPage";
import Tools from "./pages/ToolPage";

function App() {
  return (
    <Router>
      <div className="h-screen flex flex-col bg-gray-50">
        <Header />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/tools" element={<Tools />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
