import React, {useState} from 'react'

export default function Login(){
  const [email,setEmail]=useState('')
  const [pw,setPw]=useState('')
  const [msg,setMsg]=useState(null)

  function submit(e){
    e.preventDefault()
    fetch('/api/v1/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email, password: pw}), credentials:'include'})
      .then(r=>r.json()).then(()=> setMsg('Logged in')).catch(()=> setMsg('Login failed'))
  }

  return (
    <div style={{marginTop:20}}>
      <h2>Login</h2>
      <form onSubmit={submit}>
        <div><input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><input placeholder="password" type="password" value={pw} onChange={e=>setPw(e.target.value)} /></div>
        <button type="submit">Login</button>
      </form>
      {msg && <div style={{marginTop:8}}>{msg}</div>}
    </div>
  )
}
