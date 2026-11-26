import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

const NAV = {
  admin: [['/', 'Dashboard'], ['/departments', 'Departments'], ['/hods', 'HODs'], ['/faculty', 'Faculty'], ['/students', 'Students'], ['/subjects', 'Subjects'], ['/rooms', 'Rooms & Labs'], ['/sections', 'Sections'], ['/assignments', 'Subject Assignments'], ['/availability', 'Faculty Availability'], ['/constraints', 'Constraints & Periods'], ['/generate', 'Generate / Optimize'], ['/solutions', 'Compare & Pareto'], ['/timetable', 'View Timetable'], ['/edit', 'Manual Editing'], ['/conflicts', 'Conflict Reports'], ['/reopt', 'Re-optimization'], ['/approvals', 'Approvals & Publish'], ['/requests', 'Requests'], ['/reports', 'History & Export']],
  hod: [['/', 'Dashboard'], ['/faculty', 'Faculty'], ['/subjects', 'Subjects'], ['/sections', 'Sections'], ['/timetable', 'Department Timetable'], ['/conflicts', 'Conflict Reports'], ['/approvals', 'Approvals'], ['/reopt', 'Request Re-optimization'], ['/requests', 'Leave & Requests'], ['/reports', 'Export']],
  faculty: [['/', 'Dashboard'], ['/timetable', 'My Timetable'], ['/availability', 'My Availability'], ['/requests', 'Leave & Requests'], ['/reports', 'Download']],
  student: [['/', 'Dashboard'], ['/timetable', 'My Timetable'], ['/reports', 'Download PDF']],
}

export default function AppLayout() {
  const { user, logout } = useAuth(); const [open, setOpen] = useState(false)
  return (
    <div className="min-h-screen flex">
      <aside className={`${open ? 'block' : 'hidden'} md:block w-60 shrink-0 bg-navy-900 text-slate-200 fixed md:static inset-y-0 z-20 overflow-y-auto`}>
        <div className="px-4 py-4 text-white font-semibold text-lg border-b border-navy-800">AI Timetable<div className="text-xs font-normal text-slate-400">College ERP</div></div>
        <nav className="p-2 space-y-0.5">
          {NAV[user.role].map(([to, label]) => (
            <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}
              className={({ isActive }) => `block rounded-lg px-3 py-2 text-sm ${isActive ? 'bg-navy-700 text-white' : 'hover:bg-navy-800'}`}>{label}</NavLink>))}
        </nav>
      </aside>
      <div className="flex-1 min-w-0">
        <header className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <button className="md:hidden btn-ghost" onClick={() => setOpen(!open)}>Menu</button>
          <div className="text-sm text-slate-500 hidden md:block">Signed in as <b className="text-slate-800">{user.full_name}</b> <span className="ml-2 rounded-full bg-navy-50 text-navy-700 px-2 py-0.5 text-xs uppercase">{user.role}</span></div>
          <button className="btn-ghost" onClick={logout}>Logout</button>
        </header>
        <main className="p-4 md:p-6 max-w-[1400px]"><Outlet /></main>
      </div>
    </div>
  )
}
