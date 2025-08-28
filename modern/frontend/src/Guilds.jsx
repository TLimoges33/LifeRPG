import React, {useState, useEffect} from 'react'

const API = (path, opts) => fetch(path, {...(opts||{}), credentials: 'include'}).then(r=>r.json())

export default function Guilds(){
  const [guilds, setGuilds] = useState([])
  const [name, setName] = useState('')
  const [members, setMembers] = useState([])
  const [selectedGuild, setSelectedGuild] = useState(null)
  const [userId] = useState(1)

  useEffect(()=>{ API('/api/v1/guilds').then(setGuilds).catch(()=>setGuilds([])) }, [])

  function createGuild(){
    if(!name.trim()) return
    API('/api/v1/guilds', {method:'POST', body: JSON.stringify({name, owner_id: userId}), headers: {'Content-Type':'application/json'}})
      .then(g=> setGuilds([...guilds, g]))
      .catch(()=>{})
  }

  function loadMembers(gid){
    API(`/api/v1/guilds/${gid}/members`).then(setMembers).catch(()=>setMembers([]))
    setSelectedGuild(gid)
  }

  function addMember(gid){
    const uid = prompt('User ID to add:')
    if(!uid) return
    API(`/api/v1/guilds/${gid}/members`, {method:'POST', body: JSON.stringify({user_id: parseInt(uid)}), headers: {'Content-Type':'application/json'}})
      .then(()=> loadMembers(gid))
      .catch(()=> alert('failed'))
  }

  return (
    <div style={{marginTop:20}}>
      <h2>Guilds</h2>
      <div>
        <input value={name} onChange={e=>setName(e.target.value)} placeholder="Guild name" />
        <button onClick={createGuild} style={{marginLeft:8}}>Create</button>
      </div>
      <ul>
        {guilds && guilds.length ? guilds.map(g=> (
          <li key={g.id}>
            <strong>{g.name}</strong> (owner: {g.owner_id}) <button onClick={()=>loadMembers(g.id)}>Members</button>
            <button style={{marginLeft:8}} onClick={()=>addMember(g.id)}>Add Member</button>
          </li>
        )): <li>No guilds</li>}
      </ul>
      <h3>Members</h3>
      <ul>
        {members && members.length ? members.map(m=> (<li key={m.id}>User {m.user_id} — {m.role}</li>)) : <li>No members</li>}
      </ul>
    </div>
  )
}
