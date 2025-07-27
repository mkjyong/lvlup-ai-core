import React, { ErrorInfo } from 'react';
import toast from 'react-hot-toast';

interface State {
  hasError: boolean;
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('Uncaught error:', error, info);
    toast.error('예기치 못한 오류가 발생했습니다. 새로고침 후 다시 시도해주세요.');

    // Slack 알림 (환경변수에 webhook 이 설정된 경우에만)
    const webhook = import.meta.env.VITE_SLACK_WEBHOOK_ALERT_FRONTEND_ERR as string | undefined;
    if (webhook) {
      fetch(webhook, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: `:rotating_light: *Frontend Error* ${error.toString()}\n\`\`\`${info.componentStack}\`\`\``,
        }),
      }).catch(() => {
        /* ignore */
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-bg text-text">
          <p>문제가 발생했습니다.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary; 