import React, { useState, useEffect, useCallback } from 'react';
import { GitBranch, Zap, AlertTriangle, Clock, Loader2, RefreshCw, FolderOpen } from 'lucide-react';

// Utility to assign color based on severity
const severityColorMap = (severity) => {
  switch (severity) {
    case 'Critical': return 'text-red-400 bg-red-900/50 border-red-800';
    case 'High': return 'text-orange-400 bg-orange-900/50 border-orange-800';
    case 'Low': return 'text-green-400 bg-green-900/50 border-green-800';
    default: return 'text-gray-400 bg-gray-700/50 border-gray-600';
  }
};

// Utility to format time (simplified for demonstration)
const formatTimeAgo = (timestamp) => {
  const seconds = Math.floor((Date.now() - timestamp) / 1000);
  let interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + "h ago";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + "m ago";
  return Math.floor(seconds) + "s ago";
};

// Component for displaying key metrics
const RepoCard = ({ icon, title, value, detail, color = 'text-blue-400' }) => (
  <div className="p-6 bg-gray-800 rounded-xl shadow-lg border border-gray-700 hover:border-blue-500 transition duration-300">
    <div className={`text-3xl ${color}`}>{icon}</div>
    <p className="mt-2 text-sm text-gray-400 font-medium">{title}</p>
    <div className="flex items-end justify-between">
      <h3 className="text-4xl font-bold text-white mt-1">{value}</h3>
      <span className="text-sm font-semibold text-gray-500">{detail}</span>
    </div>
  </div>
);

// Component for displaying a single finding row
const LeakRow = ({ leak, index }) => {
    const status = 'Pending'; 

    // Note: We use a console log instead of alert() here as per best practices.
    const handleRemediate = () => {
        console.log(`Action: Remediation initiated for ${leak.secret_type} in ${leak.file} at line ${leak.line}.`);
        // In a real app, this would trigger a backend remediation workflow.
    };

    return (
      <tr className="border-b border-gray-700/50 hover:bg-gray-700/30 transition duration-150">
        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300 font-mono">
          {index + 1}
        </td>
        <td className="px-4 py-3 text-xs text-gray-400 font-mono max-w-xs overflow-hidden truncate" title={leak.file}>
          {leak.file} (Line {leak.line})
        </td>
        <td className="px-4 py-3 text-sm text-gray-200">
          {leak.secret_type}
        </td>
        <td className="px-4 py-3">
          <span className={`inline-flex items-center px-3 py-1 text-xs font-semibold rounded-full border ${severityColorMap(leak.severity)}`}>
            {leak.severity}
          </span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-400">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-yellow-400" />
            <span>{status}</span>
          </div>
        </td>
        <td className="px-4 py-3 text-xs text-gray-500 max-w-xs overflow-hidden truncate">
          <code className="text-[10px] bg-gray-700/50 p-1 rounded font-mono" title={leak.excerpt}>{leak.excerpt}</code>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <button
            className="text-sm text-blue-400 hover:text-blue-300 transition duration-150"
            onClick={handleRemediate}
          >
            Remediate
          </button>
        </td>
      </tr>
    );
};

// Main App Component
const App = () => {
  // Mock App ID since we don't have the actual canvas environment variables here
  const appId = 'secure-scan-app-1234'; 

  // --- State for API Integration ---
  const [directoryPath, setDirectoryPath] = useState('mock_repo'); // Default to our test repo
  const [findings, setFindings] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState(null);
  const [lastScanTimestamp, setLastScanTimestamp] = useState(null);
  const [scannedPath, setScannedPath] = useState(null);

  // Stats derived from findings
  const totalFindings = findings.length;
  const criticalFindings = findings.filter(f => f.severity === 'Critical').length;
  const highFindings = findings.filter(f => f.severity === 'High').length;


  // Function to call the Flask API
  const runApiScan = useCallback(async () => {
    if (isScanning) return;

    setIsScanning(true);
    setError(null);
    setScannedPath(null); 

    const payload = { directory_path: directoryPath };
    // IMPORTANT: This must match the address where your api_service.py is running
    const API_URL = 'http://127.0.0.1:8000/api/v1/scan';

    try {
      // 1. Send POST request to the API
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // 2. Process API response
      const data = await response.json();

      if (!response.ok || data.status === 'error') {
        throw new Error(data.error || `API Error: ${response.statusText}`);
      }

      // 3. Success! Update state with the results
      setFindings(data.findings || []);
      setLastScanTimestamp(Date.now());
      setScannedPath(data.scanned_path);

      if (data.findings_count > 0) {
        console.log(`ALERT SYSTEM: ${data.findings_count} new secrets detected in ${data.scanned_path}!`);
      }


    } catch (err) {
      console.error('Scan failed:', err);
      // Display error to the user
      setError(`Failed to connect or scan: ${err.message}. Ensure 'api_service.py' is running in the background.`);
      setFindings([]); 
    } finally {
      setIsScanning(false);
    }
  }, [directoryPath, isScanning]);
  
  // Initial scan on load
  useEffect(() => {
    if (directoryPath && findings.length === 0 && !lastScanTimestamp) {
        runApiScan();
    }
  }, [runApiScan, directoryPath, findings.length, lastScanTimestamp]);

  return (
    <div className="min-h-screen bg-gray-900 text-white font-sans p-4 sm:p-8">
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-gray-700 pb-4 mb-8">
        <h1 className="text-3xl font-extrabold text-blue-400 flex items-center">
          <Zap className="w-8 h-8 mr-2 text-yellow-500" />
          SecureScan Dashboard
          <span className="text-sm font-medium ml-3 px-3 py-1 bg-gray-700 rounded-full text-gray-300">
            App ID: {appId.substring(0, 8)}...
          </span>
        </h1>
        
        {/* Input and Scan Button */}
        <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3 w-full sm:w-auto">
            <div className="relative flex-grow">
                <input
                    type="text"
                    placeholder="Enter directory path (e.g., mock_repo)"
                    value={directoryPath}
                    onChange={(e) => setDirectoryPath(e.target.value)}
                    className="w-full px-4 py-2 pl-10 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition duration-150"
                    disabled={isScanning}
                />
                <FolderOpen className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
            </div>

            <button
                onClick={runApiScan}
                disabled={isScanning || !directoryPath}
                className={`px-4 py-2 rounded-lg text-sm font-semibold shadow-md transition duration-150 flex items-center justify-center ${isScanning ? 'bg-gray-600' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
                {isScanning ? (
                <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                ) : (
                <RefreshCw className="w-4 h-4 inline mr-2" />
                )}
                {isScanning ? 'Scanning...' : 'Run New Scan'}
            </button>
        </div>
      </header>
      
      {/* Error Display */}
      {error && (
        <div className="p-4 mb-6 text-sm text-red-100 bg-red-800 rounded-lg border border-red-700 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-3" />
            <p>{error}</p>
        </div>
      )}

      {/* Stats Cards Section */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <RepoCard
          icon={<GitBranch />}
          title="Scanned Path"
          value={scannedPath || 'N/A'}
          detail="Target directory/repository"
          color="text-blue-400"
        />
        <RepoCard
          icon={<AlertTriangle />}
          title="Critical Findings"
          value={criticalFindings}
          detail="Needs Immediate Attention"
          color="text-red-400"
        />
        <RepoCard
          icon={<Zap />}
          title="Total Findings"
          value={totalFindings}
          detail={`High Severity: ${highFindings}`}
          color="text-yellow-400"
        />
        <RepoCard
          icon={<Clock />}
          title="Last Scan"
          value={lastScanTimestamp ? formatTimeAgo(lastScanTimestamp) : 'Never'}
          detail={lastScanTimestamp ? new Date(lastScanTimestamp).toLocaleTimeString() : '...'}
          color="text-green-400"
        />
      </section>

      {/* Findings Table */}
      <section className="bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">Security Findings</h2>
          <span className="text-sm text-gray-500">Found {totalFindings} secrets</span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-700">
            <thead>
              <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider bg-gray-700/50">
                <th className="px-4 py-3">#</th>
                <th className="px-4 py-3">File Location</th>
                <th className="px-4 py-3">Secret Type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Excerpt/Context</th>
                <th className="px-4 py-3">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/50">
              {findings.length > 0 ? (
                findings.map((leak, index) => <LeakRow key={index} leak={leak} index={index} />)
              ) : (
                <tr>
                  <td colSpan="7" className="text-center py-8 text-gray-500">
                    {isScanning ? "Scanning in progress..." : "No findings reported for the last scan. Security status: Clear!"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

export default App;