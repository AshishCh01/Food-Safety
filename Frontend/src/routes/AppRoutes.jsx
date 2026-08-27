import { Route, Routes } from 'react-router-dom';
import Home from '../pages/public/Home';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import CitizenDashboard from '../pages/citizen/CitizenDashboard';
import CreateComplaint from '../pages/citizen/CreateComplaint';
import MyComplaints from '../pages/citizen/MyComplaints';
import ComplaintDetails from '../pages/citizen/ComplaintDetails';
import InspectorDashboard from '../pages/inspector/InspectorDashboard';
import AssignedComplaints from '../pages/inspector/AssignedComplaints';
import InspectionDetails from '../pages/inspector/InspectionDetails';
import InspectionHistory from '../pages/inspector/InspectionHistory';
import OfficerDashboard from '../pages/officer/OfficerDashboard';
import ComplaintQueue from '../pages/officer/ComplaintQueue';
import ComplaintReview from '../pages/officer/ComplaintReview';
import AssignInspector from '../pages/officer/AssignInspector';
import ComplaintMapPage from '../pages/officer/ComplaintMapPage';
import AdminDashboard from '../pages/admin/AdminDashboard';
import { ROLES } from '../utils/constants';
import ProtectedRoute from './ProtectedRoute';
import RoleRoute from './RoleRoute';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
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
        </Route>
      </Route>

      <Route path="*" element={<Home />} />
    </Routes>
  );
}

export default AppRoutes;
