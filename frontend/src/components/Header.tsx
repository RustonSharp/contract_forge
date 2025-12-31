import React from "react";
import { Link, useLocation } from "react-router-dom";
import { FileCheck } from "lucide-react";

const Header: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-white border-b border-gray-200 px-8 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
            <FileCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-gray-900">智能合同处理自动化系统</h1>
            <p className="text-gray-500">
              Contract Processing Automation System
            </p>
          </div>
        </div>

        <nav className="flex items-center gap-6">
          <Link
            to="/"
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive("/")
                ? "bg-blue-600 text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            首页
          </Link>
          <Link
            to="/tools"
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive("/tools")
                ? "bg-blue-600 text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            工具
          </Link>
          <Link
            to="/about"
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive("/about")
                ? "bg-blue-600 text-white"
                : "text-gray-700 hover:bg-gray-100"
            }`}
          >
            关于
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
