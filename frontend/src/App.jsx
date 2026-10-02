import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute, AdminRoute, MentorOrAdminRoute } from "./components/ProtectedRoute";

import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import Dashboard from "./pages/Dashboard";
import Questions from "./pages/Questions";
import AskQuestion from "./pages/AskQuestion";
import KnowledgeBase from "./pages/KnowledgeBase";
import AIAssistant from "./pages/AIAssistant";
import QuestionDetails from "./pages/QuestionDetails";
import Leaderboard from "./pages/Leaderboard";
import Notifications from "./pages/Notifications";
import Profile from "./pages/Profile";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminCategories from "./pages/admin/AdminCategories";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import AIReviewQueue from "./pages/AIReviewQueue";
import NotFound from "./pages/NotFound";

import "./styles/theme.css";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/questions" element={<Questions />} />
            <Route path="/questions/:id" element={<QuestionDetails />} />
            <Route path="/ask-question" element={<AskQuestion />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/notifications" element={<Notifications />} />
            <Route path="/profile" element={<Profile />} />

            <Route element={<MentorOrAdminRoute />}>
              <Route path="/ai-review-queue" element={<AIReviewQueue />} />
            </Route>

            <Route element={<AdminRoute />}>
              <Route path="/admin/users" element={<AdminUsers />} />
              <Route path="/admin/categories" element={<AdminCategories />} />
              <Route path="/admin/analytics" element={<AdminAnalytics />} />
            </Route>
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
