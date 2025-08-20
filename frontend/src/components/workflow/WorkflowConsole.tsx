import React, { useState, useEffect, useRef } from 'react';
import './WorkflowConsole.css';
interface WorkflowConsoleProps {
  sessionId?: string;
  currentStep?: string;
  isActive?: boolean;
}
export const WorkflowConsole: React.FC<WorkflowConsoleProps> = ({
  sessionId,
  currentStep,
  isActive = false
}) => {
  const [logs, setLogs] = useState<string[]>([]);
  const [llmResponse, setLlmResponse] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const consoleRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs, llmResponse, autoScroll]);
  // 获取工作流日志
  useEffect(() => {
    if (!sessionId || !isActive) return;
    const fetchLogs = async () => {
      try {
        const response = await fetch(`/api/v1/workflow/logs/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.logs && Array.isArray(data.logs)) {
            setLogs(data.logs);
          }
        }
      } catch (error) {
        console.error('Failed to fetch logs:', error);
      }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [sessionId, isActive]);
  // 在调试循环阶段分析Pipeline日志
  useEffect(() => {
    if (currentStep === 'debug_loop' && logs.length > 0 && !isAnalyzing) {
      // 检查日志中是否有Pipeline失败信息
      const hasFailure = logs.some(log => 
        log.toLowerCase().includes('failed') || 
        log.toLowerCase().includes('error') ||
        log.toLowerCase().includes('pipeline有任务失败')
      );
      if (hasFailure) {
        analyzePipelineLogs();
      }
    }
  }, [currentStep, logs, isAnalyzing]);
  const analyzePipelineLogs = async () => {
    if (isAnalyzing) return;
    setIsAnalyzing(true);
    setLlmResponse('');
    try {
      // 获取最新的日志内容
      const recentLogs = logs.slice(-20).join('\n');
      const response = await fetch('/api/v1/llm/analyze-logs-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logs: recentLogs
        })
      });
      if (!response.ok) {
        throw new Error('Failed to start log analysis');
      }
      // 关闭之前的连接
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      // 使用fetch流式API
      const reader = response.body?.getReader();
      if (reader) {
        const decoder = new TextDecoder();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'content') {
                  setLlmResponse(prev => prev + data.content);
                } else if (data.type === 'done') {
                  setIsAnalyzing(false);
                  return;
                } else if (data.type === 'error') {
                  setLlmResponse(prev => prev + `\n[错误] ${data.content}`);
                  setIsAnalyzing(false);
                  return;
                }
              } catch (error) {
                console.error('Failed to parse streaming data:', error);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to analyze logs:', error);
      setLlmResponse(`分析日志时出错: ${error instanceof Error ? error.message : String(error)}`);
      setIsAnalyzing(false);
    }
  };
  // 清理EventSource
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);
  const clearConsole = () => {
    setLogs([]);
    setLlmResponse('');
  };
  const formatLogLine = (log: string, index: number) => {
    // 检测不同类型的日志行
    if (log.includes('[ERROR]') || log.includes('ERROR') || log.includes('failed')) {
      return <div key={index} className="log-line error">{log}</div>;
    } else if (log.includes('[WARN]') || log.includes('WARNING')) {
      return <div key={index} className="log-line warning">{log}</div>;
    } else if (log.includes('[INFO]') || log.includes('SUCCESS')) {
      return <div key={index} className="log-line info">{log}</div>;
    } else if (log.includes('[DEBUG]')) {
      return <div key={index} className="log-line debug">{log}</div>;
    } else {
      return <div key={index} className="log-line">{log}</div>;
    }
  };
  return (
    <div className="workflow-console">
      <div className="console-header">
        <h3>实时执行日志</h3>
        <div className="console-controls">
          <label className="auto-scroll-toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            自动滚动
          </label>
          <button onClick={clearConsole} className="btn btn-secondary btn-small">
            清空
          </button>
          {currentStep === 'debug_loop' && (
            <button 
              onClick={analyzePipelineLogs} 
              disabled={isAnalyzing}
              className="btn btn-primary btn-small"
            >
              {isAnalyzing ? '分析中...' : '分析日志'}
            </button>
          )}
        </div>
      </div>
      <div className="console-content" ref={consoleRef}>
        {/* 工作流日志 */}
        <div className="logs-section">
          <div className="section-header">
            <span className="section-title">📋 工作流日志</span>
            <span className="log-count">{logs.length} 条</span>
          </div>
          <div className="log-lines">
            {logs.length === 0 ? (
              <div className="no-logs">暂无日志信息</div>
            ) : (
              logs.map((log, index) => formatLogLine(log, index))
            )}
          </div>
        </div>
        {/* LLM分析结果 */}
        {(llmResponse || isAnalyzing) && (
          <div className="llm-section">
            <div className="section-header">
              <span className="section-title">🤖 AI分析结果</span>
              {isAnalyzing && <span className="analyzing-indicator">分析中...</span>}
            </div>
            <div className="llm-response">
              {isAnalyzing && !llmResponse && (
                <div className="analyzing-placeholder">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  正在分析Pipeline日志，请稍候...
                </div>
              )}
              {llmResponse && (
                <div className="response-content">
                  {llmResponse.split('\n').map((line, index) => (
                    <div key={index} className="response-line">{line}</div>
                  ))}
                  {isAnalyzing && <span className="cursor">|</span>}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};