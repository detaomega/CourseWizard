import { Routes, Route } from "react-router-dom";
import HomePage from "./views/home/HomePage";

const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />

      {/* More route... */}
    </Routes>
  );
};

export default App;
