import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import PublicLayout from '../components/layout/PublicLayout';
import Spinner from '../components/ui/Spinner';
import { ROLES } from '../utils/constants';
import ProtectedRoute from './ProtectedRoute';
import RoleRoute from './RoleRoute';

// Route-level code splitting: each page (and the heavier libraries only it
// needs, e.g. recharts for the officer/admin dashboards, leaflet for the
// map-touching pages) loads on demand instead of in the initial bundle.
const Home = lazy(() => import('../pages/public/Home'));
const NotFound = lazy(() => import('../pages/public/NotFound'));
const Login = lazy(() => import('../pages/auth/Login'));
const Register = lazy(() => import('../pages/auth/Register'));

const CitizenDashboard = lazy(() => import('../pages/citizen/CitizenDashboard'));
const CreateComplaint = lazy(() => import('../pages/citizen/CreateComplaint'));
const MyComplaints = lazy(() => import('../pages/citizen/MyComplaints'));
const ComplaintDetails = lazy(() => import('../pages/citizen/ComplaintDetails'));

const InspectorDashboard = lazy(() => import('../pages/inspector/InspectorDashboard'));
const AssignedComplaints = lazy(() => import('../pages/inspector/AssignedComplaints'));
const InspectionDetails = lazy(() => import('../pages/inspector/InspectionDetails'));
const InspectionHistory = lazy(() => import('../pages/inspector/InspectionHistory'));
const InspectorAssistant = lazy(() => import('../pages/inspector/InspectorAssistant'));

const OfficerDashboard = lazy(() => import('../pages/officer/OfficerDashboard'));
const ComplaintQueue = lazy(() => import('../pages/officer/ComplaintQueue'));
const ComplaintReview = lazy(() => import('../pages/officer/ComplaintReview'));
const AssignInspector = lazy(() => import('../pages/officer/AssignInspector'));
const ComplaintMapPage = lazy(() => import('../pages/officer/ComplaintMapPage'));

const AdminDashboard = lazy(() => import('../pages/admin/AdminDashboard'));
const AuditLogs = lazy(() => import('../pages/admin/AuditLogs'));
const StaffManagement = lazy(() => import('../pages/admin/StaffManagement'));
const Businesses = lazy(() => import('../pages/admin/Businesses'));
const RagDocuments = lazy(() => import('../pages/admin/RagDocuments'));

const Notifications = lazy(() => import('../pages/shared/Notifications'));

function RouteFallback() {
  return (
    <div className="flex min-h-64 items-center justify-center">
      <Spinner label="Loading…" />
    </div>
  );
}

function AppRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/notifications" element={<Notifications />} />
            <Route element={<RoleRoute allowedRoles={[ROLES.CITIZEN]} />}>
              <Route path="/citizen" element={<CitizenDashboard />} />
              <Route path="/citizen/complaints" element={<MyComplaints />} />
              <Route path="/citizen/complaints/new" element={<CreateComplaint />} />
              <Route path="/citizen/complaints/:complaintId" element={<ComplaintDetails />} />
            </Route>
            <Route element={<RoleRoute allowedRoles={[ROLES.INSPECTOR]} />}>
              <Route path="/inspector" element={<InspectorDashboard />} />
              <Route path="/inspector/assignments" element={<AssignedComplaints />} />
              <Route path="/inspector/assignments/:assignmentId" element={<InspectionDetails />} />
              <Route path="/inspector/history" element={<InspectionHistory />} />
              <Route path="/inspector/assistant" element={<InspectorAssistant />} />
            </Route>
            <Route element={<RoleRoute allowedRoles={[ROLES.DISTRICT_OFFICER]} />}>
              <Route path="/officer" element={<OfficerDashboard />} />
              <Route path="/officer/map" element={<ComplaintMapPage />} />
              <Route path="/officer/complaints" element={<ComplaintQueue />} />
              <Route path="/officer/complaints/:complaintId" element={<ComplaintReview />} />
              <Route path="/officer/complaints/:complaintId/assign" element={<AssignInspector />} />
            </Route>
            <Route element={<RoleRoute allowedRoles={[ROLES.ADMIN]} />}>
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/admin/staff" element={<StaffManagement />} />
              <Route path="/admin/businesses" element={<Businesses />} />
              <Route path="/admin/rag-documents" element={<RagDocuments />} />
              <Route path="/admin/audit-logs" element={<AuditLogs />} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </Suspense>
  );
}

export default AppRoutes;
