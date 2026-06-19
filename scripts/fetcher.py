<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Spread | Daily Intelligence Terminal</title>

<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone@7.23.6/babel.min.js"></script>
<script src="https://cdn.tailwindcss.com"></script>

<style>
  :root {
    --canvas: #EEF0F3;
    --canvas-alt: #E5E7EB;
    --ink: #14151A;
    --ink-soft: #5A5C66;
    --ink-faint: #8A8C95;
    --hairline: rgba(20,21,26,0.09);
    
    /* Liquid Glass Constants */
    --glass-bg: rgba(255,255,255,0.55);
    --glass-bg-strong: rgba(255,255,255,0.74);
    --glass-border: rgba(255,255,255,0.7);
    --glass-shadow: rgba(20,21,26,0.08);
    
    --brass: #A9824C;
    --brass-soft: rgba(169,130,76,0.14);
    
    /* Jurisprudential Spectrum Colors */
    --lean-left: #2F62D6;
    --lean-left-bg: rgba(47,98,214,0.09);
    --lean-center: #756AA0;
    --lean-center-bg: rgba(117,106,160,0.09);
    --lean-right: #B3473A;
    --lean-right-bg: rgba(179,71,58,0.09);
    
    /* Typography */
    --font-display: -apple-system, "SF Pro Display", "Helvetica Neue", system-ui, sans-serif;
    --font-body: -apple-system, "SF Pro Text", system-ui, sans-serif;
    --font-serif: ui-serif, "New York", "Iowan Old Style", Georgia, serif;
  }

  [data-theme="dark"] {
    --canvas: #000000;
    --canvas-alt: #0A0A0C;
    --ink: #F2F2F4;
    --ink-soft: #A0A2AC;
    --ink-faint: #6E707A;
    --hairline: rgba(255,255,255,0.10);
    
    --glass-bg: rgba(30,30,34,0.55);
    --glass-bg-strong: rgba(34,34,38,0.76);
    --glass-border: rgba(255,255,255,0.09);
    --glass-shadow: rgba(0,0,0,0.55);
    
    --brass: #CDA66E;
    --brass-soft: rgba(205,166,110,0.16);
    --lean-left: #6892F2; --lean-left-bg: rgba(104,146,242,0.14);
    --lean-center: #A498D0; --lean-center-bg: rgba(164,152,208,0.14);
    --lean-right: #D6837A; --lean-right-bg: rgba(214,131,122,0.14);
  }

  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
  body { background: var(--canvas); font-family: var(--font-body); color: var(--ink); -webkit-font-smoothing: antialiased; transition: background 0.3s ease, color 0.3s ease; }

  .desktop-layout { display: grid; grid-template-columns: 260px 1fr; height: 100vh; }

  .sidebar { background: var(--glass-bg-strong); backdrop-filter: blur(24px) saturate(180%); -webkit-backdrop-filter: blur(24px) saturate(180%); border-right: 1px solid var(--hairline); display: flex; flex-direction: column; padding: 24px 16px; z-index: 50; }
  .wordmark { font-family: var(--font-display); font-weight: 800; font-size: 24px; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px; margin-bottom: 40px; padding-left: 8px; }
  .wordmark .tick { width: 12px; height: 3px; background: var(--brass); border-radius: 2px; }

  .nav-group { margin-bottom: 32px; }
  .nav-label { font-size: 11px; font-weight: 700; color: var(--ink-faint); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px; padding-left: 12px; }
  
  .nav-item { display: flex; align-items: center; gap: 10px; width: 100%; appearance: none; border: none; background: transparent; color: var(--ink-soft); font-size: 14px; font-weight: 500; font-family: var(--font-body); padding: 8px 12px; border-radius: 8px; cursor: pointer; text-align: left; transition: all 0.2s; }
  .nav-item:hover { background: var(--hairline); color: var(--ink); }
  .nav-item.active { background: var(--glass-bg); border: 1px solid var(--glass-border); color: var(--ink); box-shadow: 0 4px 12px var(--glass-shadow); font-weight: 600; }
  .nav-count { font-size: 11px; font-family: monospace; opacity: 0.5; background: var(--hairline); padding: 2px 6px; border-radius: 6px; margin-left: auto; }

  .main-stage { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

  .topbar { height: 72px; padding: 0 40px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--hairline); background: var(--canvas); z-index: 40; }
  .search-bar { display: flex; align-items: center; gap: 10px; background: var(--glass-bg); border: 1px solid var(--glass-border); padding: 8px 16px; border-radius: 100px; width: 400px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02); }
  .search-bar input { border: none; background: transparent; outline: none; color: var(--ink); font-family: var(--font-body); font-size: 14px; width: 100%; }
  .search-bar input::placeholder { color: var(--ink-faint); }

  .topbar-actions { display: flex; align-items: center; gap: 12px; }
  .btn-icon { appearance: none; border: 1px solid var(--hairline); background: var(--glass-bg); color: var(--ink); padding: 8px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
  .btn-icon:hover { background: var(--hairline); }

  .scroll-area { flex: 1; overflow-y: auto; padding: 40px 40px 100px; }

  .glass-card { position: relative; border-radius: 20px; margin-bottom: 24px; z-index: 1; height: 100%; display: flex; flex-direction: column; }
  .glass-layers { position: absolute; inset: 0; border-radius: 20px; overflow: hidden; box-shadow: 0 12px 32px var(--glass-shadow); z-index: -1; }
  .glass-filter { position: absolute; inset: 0; background: var(--glass-bg); backdrop-filter: blur(24px) saturate(180%); -webkit-backdrop-filter: blur(24px) saturate(180%); }
  .glass-overlay { position: absolute; inset: -50px; background: radial-gradient(circle at 0% 0%, rgba(255,255,255,0.3) 0%, transparent 60%); filter: url(#glass-distortion); opacity: 0.25; pointer-events: none; mix-blend-mode: overlay; }
  .glass-specular { position: absolute; inset: 0; border: 1px solid var(--glass-border); border-radius: 20px; box-shadow: inset 0 1px 1px rgba(255,255,255,0.3); pointer-events: none; }
  
  .glass-card.docket .glass-specular { border-left: 4px solid var(--brass); }
  .glass-content { position: relative; padding: 24px; z-index: 2; flex: 1; display: flex; flex-direction: column; }

  .eyebrow-tag { font-family: var(--font-display); font-weight: 700; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--brass); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
  .eyebrow-tag .source-text { color: var(--ink-faint); }
  .headline { font-family: var(--font-display); font-weight: 700; font-size: 19px; line-height: 1.25; letter-spacing: -0.2px; margin: 0 0 10px; }
  .snippet { font-size: 14.5px; line-height: 1.5; color: var(--ink-soft); margin: 0 0 16px; flex: 1; }
  .byline { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--ink-faint); margin-bottom: 16px; }

  .grid-2-col { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 24px; margin-bottom: 40px; }

  .bias-hit-area { padding: 10px 0; margin: -10px 0 0 0; cursor: crosshair; }
  .biasbar { display: flex; height: 8px; border-radius: 5px; overflow: hidden; border: 1px solid var(--hairline); transition: transform 0.2s ease; }
  .biasbar span { display: block; height: 100%; transition: filter 0.3s ease, transform 0.2s ease; }
  
  .bias-hit-area:hover .biasbar span { filter: grayscale(0.5) opacity(0.5); }
  .bias-hit-area:hover .biasbar span.active { filter: grayscale(0) opacity(1) brightness(1.1); transform: scaleY(1.3); }

  .seg-left { background: var(--lean-left); } .seg-center { background: var(--lean-center); } .seg-right { background: var(--lean-right); }

  .leanwrap { display: flex; flex-direction: column; }
  .leanrow { border-radius: 11px; font-size: 12.5px; line-height: 1.5; max-height: 0; opacity: 0; overflow: hidden; padding: 0 12px; margin-bottom: 0; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
  .leanrow.expanded { max-height: 250px; opacity: 1; padding: 12px 14px; margin-bottom: 8px; margin-top: 12px; }
  
  .leanrow .tag { font-family: var(--font-display); font-weight: 700; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px; display: block; }
  .leanrow.l { background: var(--lean-left-bg); border-left: 3px solid var(--lean-left); } .leanrow.l .tag { color: var(--lean-left); }
  .leanrow.c { background: var(--lean-center-bg); border-left: 3px solid var(--lean-center); } .leanrow.c .tag { color: var(--lean-center); }
  .leanrow.r { background: var(--lean-right-bg); border-left: 3px solid var(--lean-right); } .leanrow.r .tag { color: var(--lean-right); }

  .neutral { border-top: 1px solid var(--hairline); padding-top: 12px; margin-top: 12px; font-family: var(--font-serif); font-style: italic; font-size: 13.5px; color: var(--ink-soft); line-height: 1.5; }
  .neutral b { font-style: normal; color: var(--ink); font-weight: 600; }

  .knowledge-mapping { margin-bottom: 16px; padding: 12px; background: var(--canvas-alt); border-radius: 12px; border: 1px solid var(--hairline); }
  .mapping-title { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--ink-faint); margin-bottom: 8px; display: flex; align-items: center; gap: 4px; }
  .tags { display: flex; flex-wrap: wrap; gap: 6px; }
  .tagpill { font-size: 11.5px; padding: 4px 10px; border: 1px solid var(--hairline); border-radius: 100px; color: var(--ink-soft); background: var(--glass-bg); display: flex; align-items: center; gap: 4px; }

  .card-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--hairline); }
  .source-link-btn { font-size: 12px; font-weight: 600; color: var(--ink-soft); text-decoration: none; display: flex; align-items: center; gap: 6px; transition: color 0.2s; }
  .source-link-btn:hover { color: var(--ink); }
  
  .action-btn { appearance: none; background: transparent; border: 1px solid var(--hairline); color: var(--ink-soft); padding: 6px 12px; border-radius: 100px; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; transition: all 0.2s; }
  .action-btn:hover { background: var(--glass-bg-strong); color: var(--ink); }

  .loader-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; gap: 16px; color: var(--ink-faint); font-family: monospace; font-size: 14px; }
  .loader-spinner { animation: spin 1s linear infinite; }
  @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

<svg style="display: none">
  <filter id="glass-distortion">
    <feTurbulence type="turbulence" baseFrequency="0.008" numOctaves="2" result="noise" />
    <feDisplacementMap in="SourceGraphic" in2="noise" scale="77" />
  </filter>
</svg>

<div id="root"></div>

<script type="text/babel">
  const { useState, useEffect, useMemo } = React;

  // Safe Native SVG Icons
  const IconDashboard = () => <svg className="inline mr-2" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="11" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>;
  const IconScale = () => <svg className="inline mr-2" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/></svg>;
  const IconSearch = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>;
  const IconMerge = () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m8 6 4-4 4 4"/><path d="M12 2v10.3a4 4 0 0 1-1.172 2.872L4 22"/><path d="m20 22-5-5"/></svg>;
  const IconHash = () => <svg width="10" height="10" opacity="0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/></svg>;
  const IconExternal = () => <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" x1="21" y1="14" y2="3"/></svg>;
  const IconBookmark = ({ check }) => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>{check && <polyline points="9 10 12 13 16 9"/>}</svg>;
  const IconMode = ({ dark }) => dark ? <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg> : <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>;
  const IconLoader = () => <svg className="loader-spinner" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>;
  const IconCrash = () => <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2Values"/><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M12 17v4"/><path d="M8 21h8"/></svg>;

  const BiasSpectrum = ({ data }) => {
    const [hovered, setHovered] = useState(null);
    if (!data || !data.baseline) return null;

    return (
      <div className="mt-2">
        <div className="bias-hit-area" onMouseLeave={() => setHovered(null)}>
          <div className="biasbar">
            <span className={`seg-left ${hovered === 'l' ? 'active' : ''}`} style={{ width: `${data.baseline.left}%` }} onMouseEnter={() => setHovered('l')} />
            <span className={`seg-center ${hovered === 'c' ? 'active' : ''}`} style={{ width: `${data.baseline.center}%` }} onMouseEnter={() => setHovered('c')} />
            <span className={`seg-right ${hovered === 'r' ? 'active' : ''}`} style={{ width: `${data.baseline.right}%` }} onMouseEnter={() => setHovered('r')} />
          </div>
          <div className="leanwrap">
            <div className={`leanrow l ${hovered === 'l' ? 'expanded' : ''}`}><span className="tag">{data.zones?.left?.label}</span>{data.zones?.left?.synthesis}</div>
            <div className={`leanrow c ${hovered === 'c' ? 'expanded' : ''}`}><span className="tag">{data.zones?.center?.label}</span>{data.zones?.center?.synthesis}</div>
            <div className={`leanrow r ${hovered === 'r' ? 'expanded' : ''}`}><span className="tag">{data.zones?.right?.label}</span>{data.zones?.right?.synthesis}</div>
          </div>
        </div>
        {data.neutral && <div className="neutral"><b>Objective Synthesis:</b> {data.neutral}</div>}
      </div>
    );
  };

  const StoryCard = ({ story, isArchived, onToggleArchive }) => {
    const searchFallbackUrl = `https://www.google.com/search?q=${encodeURIComponent(story.title + ' ' + (story.source || ''))}`;
    
    return (
      <div className={`glass-card ${(story.source || '').includes('Court') ? 'docket' : ''}`}>
        <div className="glass-layers"><div className="glass-filter"></div><div className="glass-overlay"></div></div>
        <div className="glass-specular"></div>
        <div className="glass-content">
          <div className="eyebrow-tag">
            <span>{story.category || 'Intelligence'}</span>
            <span className="source-text">{story.source || 'Network Scan'}</span>
          </div>
          
          <h2 className="headline">{story.title}</h2>
          <div className="byline text-xs font-mono opacity-60 mb-2">{story.citation || 'Live Triage'}</div>
          <p className="snippet">{story.summary}</p>
          
          {story.graph && story.graph.length > 0 && (
            <div className="knowledge-mapping">
              <div className="mapping-title"><IconMerge /> Knowledge Graph Mapping</div>
              <div className="tags">
                {story.graph.map(t => <span key={t} className="tagpill"><IconHash /> {t}</span>)}
              </div>
            </div>
          )}
          
          <BiasSpectrum data={story.spectrum} />

          <div className="card-actions">
            <a href={story.url || searchFallbackUrl} target="_blank" rel="noopener noreferrer" className="source-link-btn">
              <IconExternal /> Read Source
            </a>
            <button className={`action-btn ${isArchived ? 'archived' : ''}`} onClick={() => onToggleArchive(story.id || story.title)}>
              <IconBookmark check={isArchived} />
              {isArchived ? 'Archived' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const App = () => {
    const [theme, setTheme] = useState('dark');
    const [activeView, setActiveView] = useState('briefing');
    const [dataStore, setDataStore] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    
    const [archivedIds, setArchivedIds] = useState(() => {
      const saved = localStorage.getItem('spread_dossier');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    });

    useEffect(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);
    useEffect(() => { localStorage.setItem('spread_dossier', JSON.stringify(Array.from(archivedIds))); }, [archivedIds]);

    useEffect(() => {
      const fetchLiveIntelligence = async () => {
        try {
          const res = await fetch(`database.json?v=${new Date().getTime()}`);
          if (!res.ok) throw new Error("Awaiting Daily AI Build...");
          const liveData = await res.json();
          setDataStore(liveData);
        } catch (err) {
          console.error("Database connection failure:", err);
        } finally {
          setIsLoading(false);
        }
      };
      fetchLiveIntelligence();
    }, []);

    const toggleArchive = (id) => {
      const newSet = new Set(archivedIds);
      if (newSet.has(id)) newSet.delete(id); else newSet.add(id);
      setArchivedIds(newSet);
    };

    const storiesToShow = useMemo(() => {
      if (!dataStore) return [];
      if (activeView === 'briefing') {
        return [
          ...(dataStore.federalism?.slice(0, 3) || []),
          ...(dataStore.charter?.slice(0, 3) || []),
          ...(dataStore.indigenous?.slice(0, 3) || []),
          ...(dataStore.criminal?.slice(0, 3) || []),
          ...(dataStore.immigration?.slice(0, 3) || [])
        ];
      }
      if (activeView === 'scc') {
        const allStories = [
          ...(dataStore.federalism || []),
          ...(dataStore.charter || []),
          ...(dataStore.indigenous || []),
          ...(dataStore.criminal || []),
          ...(dataStore.immigration || [])
        ];
        return allStories.filter(story => {
          const src = (story.source || '').toLowerCase();
          return src.includes('supreme court') || src.includes('scc');
        });
      }
      return dataStore[activeView] || [];
    }, [activeView, dataStore]);

    const getCount = (cat) => dataStore?.[cat]?.length || 0;

    return (
      <div className="desktop-layout">
        
        <nav className="sidebar">
          <div className="wordmark"><span className="tick"></span>The Spread</div>
          
          <div className="nav-group">
            <div className="nav-label">Intelligence</div>
            <button className={`nav-item ${activeView === 'briefing' ? 'active' : ''}`} onClick={() => setActiveView('briefing')}>
              <IconDashboard /> Daily Briefing
            </button>
            <button className={`nav-item ${activeView === 'scc' ? 'active' : ''}`} onClick={() => setActiveView('scc')}>
              <IconScale /> SCC Fridays
            </button>
          </div>

          <div className="nav-group">
            <div className="nav-label">Subjects</div>
            <button className={`nav-item ${activeView === 'federalism' ? 'active' : ''}`} onClick={() => setActiveView('federalism')}>
              Federalism {dataStore && <span className="nav-count">{getCount('federalism')}</span>}
            </button>
            <button className={`nav-item ${activeView === 'charter' ? 'active' : ''}`} onClick={() => setActiveView('charter')}>
              Charter {dataStore && <span className="nav-count">{getCount('charter')}</span>}
            </button>
            <button className={`nav-item ${activeView === 'indigenous' ? 'active' : ''}`} onClick={() => setActiveView('indigenous')}>
              Indigenous {dataStore && <span className="nav-count">{getCount('indigenous')}</span>}
            </button>
            <button className={`nav-item ${activeView === 'criminal' ? 'active' : ''}`} onClick={() => setActiveView('criminal')}>
              Criminal Law {dataStore && <span className="nav-count">{getCount('criminal')}</span>}
            </button>
            <button className={`nav-item ${activeView === 'immigration' ? 'active' : ''}`} onClick={() => setActiveView('immigration')}>
              Immigration {dataStore && <span className="nav-count">{getCount('immigration')}</span>}
            </button>
          </div>
        </nav>

        <main className="main-stage">
          <header className="topbar">
            <div className="search-bar">
              <IconSearch />
              <input type="text" placeholder="Semantic search disabled during triage..." disabled />
            </div>

            <div className="topbar-actions">
              <button className="btn-icon" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                <IconMode dark={theme === 'dark'} />
              </button>
            </div>
          </header>

          <div className="scroll-area">
            {isLoading ? (
              <div className="loader-container">
                <IconLoader />
                <p>Establishing secure connection to live intelligence database...</p>
              </div>
            ) : !dataStore ? (
              <div className="loader-container">
                <IconCrash />
                <p>Waiting for the 8:00 AM Gemini build to finish generating database.json...</p>
              </div>
            ) : (
              <>
                {activeView === 'briefing' && (
                  <div className="mb-8 pl-2">
                    <h1 className="text-2xl font-bold tracking-tight mb-1">The Daily Briefing</h1>
                    <p className="text-sm opacity-60">High-density apex intelligence from the 8:00 AM pipeline.</p>
                  </div>
                )}
                {activeView === 'scc' && (
                  <div className="mb-8 pl-2">
                    <h1 className="text-2xl font-bold tracking-tight mb-1">SCC Fridays</h1>
                    <p className="text-sm opacity-60">Exclusive tracking for Supreme Court of Canada judgments and precedent shifts.</p>
                  </div>
                )}
                
                {/* Fallback header for normal categories */}
                {activeView !== 'briefing' && activeView !== 'scc' && (
                  <div className="mb-8 pl-2">
                    <h1 className="text-2xl font-bold tracking-tight mb-1 capitalize">{activeView}</h1>
                    <p className="text-sm opacity-60">Recent structural updates in this domain.</p>
                  </div>
                )}
                
                <div className="grid-2-col">
                  {storiesToShow.length > 0 ? storiesToShow.map(story => (
                    <StoryCard 
                      key={story.id || Math.random()} 
                      story={story} 
                      isArchived={archivedIds.has(story.id || story.title)} 
                      onToggleArchive={toggleArchive} 
                    />
                  )) : (
                    <div className="col-span-full text-center opacity-50 mt-10 font-mono text-sm">
                      No critical structural updates detected in this domain over the last 24 hours.
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    );
  };

  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(<App />);
</script>
</body>
</html>
