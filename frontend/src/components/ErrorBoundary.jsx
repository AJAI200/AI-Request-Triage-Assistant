import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled rendering error:", error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#FFF8EE] flex items-center justify-center p-6 text-[#2D1F17]">
          <div className="pill-card max-w-md w-full p-8 text-center space-y-5 bg-white border-2 border-rose-200 shadow-2xl">
            <div className="w-14 h-14 rounded-3xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto shadow-sm">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-[#2D1F17]">Application Interface Error</h2>
              <p className="text-xs text-[#7A6B63] mt-1 leading-relaxed">
                An unexpected component rendering error occurred. The application state was safely isolated to prevent data loss.
              </p>
            </div>
            <div className="pt-2">
              <button
                type="button"
                onClick={this.handleReload}
                className="pill-btn btn-orange w-full py-3 text-sm font-extrabold flex items-center justify-center gap-2 shadow-lg"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reload Workspace</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
