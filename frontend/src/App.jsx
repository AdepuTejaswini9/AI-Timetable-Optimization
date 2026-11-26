import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import AppLayout from './layouts/AppLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import TimetableView from './pages/TimetableView'
import Generate from './pages/Generate'
import Solutions from './pages/Solutions'
import { Conflicts, ManualEdit, Reopt } from './pages/Review'
import Approvals from './pages/Approvals'
import Requests from './pages/Requests'
import Availability from './pages/Availability'
import Constraints from './pages/Constraints'
import Reports from './pages/Reports'
import { Departments, Hods, Faculty, Students, Subjects, Rooms, Sections, Assignments } from './pages/Masters'

const A = ['admin'], AH = ['admin', 'hod'], AF = ['admin', 'faculty'], NS = ['admin', 'hod', 'faculty'], ALL = ['admin', 'hod', 'faculty', 'student']
function Guard({ roles, children }) {
  const { user } = useAuth()
  return roles.includes(user.role) ? children : <div className="card text-red-700">You do not have access to this page.</div>   // backend enforces too
}
export default function App() {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>
  if (!user) return <Routes><Route path="/login" element={<Login />} /><Route path="*" element={<Navigate to="/login" replace />} /></Routes>
  const R = (path, roles, el) => <Route path={path} element={<Guard roles={roles}>{el}</Guard>} />
  return <Routes><Route path="/login" element={<Navigate to="/" replace />} /><Route element={<AppLayout />}>
    {R('/', ALL, <Dashboard />)}{R('/departments', A, <Departments />)}{R('/hods', A, <Hods />)}{R('/faculty', AH, <Faculty />)}{R('/students', A, <Students />)}
    {R('/subjects', AH, <Subjects />)}{R('/rooms', A, <Rooms />)}{R('/sections', AH, <Sections />)}{R('/assignments', A, <Assignments />)}
    {R('/availability', AF, <Availability />)}{R('/constraints', A, <Constraints />)}{R('/generate', A, <Generate />)}{R('/solutions', A, <Solutions />)}
    {R('/timetable', ALL, <TimetableView />)}{R('/edit', A, <ManualEdit />)}{R('/conflicts', AH, <Conflicts />)}{R('/reopt', AH, <Reopt />)}
    {R('/approvals', AH, <Approvals />)}{R('/requests', NS, <Requests />)}{R('/reports', ALL, <Reports />)}
    <Route path="*" element={<Navigate to="/" replace />} /></Route></Routes>
}
