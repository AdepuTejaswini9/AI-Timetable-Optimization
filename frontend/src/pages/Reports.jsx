import { download } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { Badge, Table, useLoad } from '../components/ui'
export default function Reports() {
  const { user } = useAuth(); const [vs] = useLoad('/timetable')
  return <div><h1 className="h1">{user.role === 'admin' ? 'Timetable History & Export' : 'Download Timetable'}</h1>
    <div className="card p-0"><Table cols={[{ key: 'id', label: '#' }, { key: 'name', label: 'Name' }, { label: 'Status', render: (v) => <Badge v={v.status} /> }, { key: 'version_number', label: 'Version' }, { key: 'parent_version_id', label: 'Parent' }, { label: 'Created', render: (v) => v.created_at?.slice(0, 16).replace('T', ' ') },
      { label: 'Export', render: (v) => <span className="space-x-2"><button className="btn-ghost" onClick={() => download(`/export/timetable/${v.id}/pdf`, `timetable_${v.id}.pdf`)}>PDF</button>{user.role !== 'student' && <button className="btn-ghost" onClick={() => download(`/export/timetable/${v.id}/excel`, `timetable_${v.id}.xlsx`)}>Excel</button>}</span> }]} rows={vs || []} empty="No timetables available" /></div></div>
}
