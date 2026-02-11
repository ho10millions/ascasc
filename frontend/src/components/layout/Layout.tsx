import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function Layout() {
  return (
    <div className="min-h-screen flex noise">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-72">
        <Navbar />
        <main className="flex-1 p-8 grid-pattern">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
