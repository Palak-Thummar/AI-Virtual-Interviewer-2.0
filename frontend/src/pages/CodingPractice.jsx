import React, { useEffect, useMemo, useRef, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Loader2 } from 'lucide-react';
import { codingAPI } from '../services/api';
import styles from './CodingPractice.module.css';

const DEFAULT_TEMPLATE = 'def solve():\n    pass\n';

const difficultyClassMap = {
  Easy: styles.badgeEasy,
  Medium: styles.badgeMedium,
  Hard: styles.badgeHard
};

const resultClassMap = {
  passed: styles.statusPassed,
  failed: styles.statusFailed
};

const safeParse = (value, fallback) => {
  try {
    return JSON.parse(value) ?? fallback;
  } catch {
    return fallback;
  }
};

export const CodingPracticePage = () => {
  const [problems, setProblems] = useState([]);
  const [selectedProblemId, setSelectedProblemId] = useState('');
  const [language, setLanguage] = useState('python');
  const [codeByProblem, setCodeByProblem] = useState({});
  const [result, setResult] = useState(null);
  const [loadingProblems, setLoadingProblems] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const editorRef = useRef(null);

  useEffect(() => {
    const savedCodes = safeParse(localStorage.getItem('coding_practice_codes'), {});
    const savedLanguage = localStorage.getItem('coding_practice_language');
    const savedProblemId = localStorage.getItem('coding_practice_problem_id');

    setCodeByProblem(savedCodes);
    if (savedLanguage) setLanguage(savedLanguage);
    if (savedProblemId) setSelectedProblemId(savedProblemId);
  }, []);

  useEffect(() => {
    const fetchProblems = async () => {
      try {
        setLoadingProblems(true);
        setError('');
        const response = await codingAPI.getProblems();
        const list = response?.data || [];
        setProblems(Array.isArray(list) ? list : []);

        if (!selectedProblemId && Array.isArray(list) && list.length > 0) {
          const savedProblemId = localStorage.getItem('coding_practice_problem_id');
          const targetId = savedProblemId && list.some((item) => item.id === savedProblemId)
            ? savedProblemId
            : '';
          setSelectedProblemId(targetId);
        }
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to load coding problems.');
      } finally {
        setLoadingProblems(false);
      }
    };

    fetchProblems();
  }, []);

  useEffect(() => {
    localStorage.setItem('coding_practice_codes', JSON.stringify(codeByProblem));
  }, [codeByProblem]);

  useEffect(() => {
    localStorage.setItem('coding_practice_language', language);
  }, [language]);

  useEffect(() => {
    if (selectedProblemId) {
      localStorage.setItem('coding_practice_problem_id', selectedProblemId);
    }
  }, [selectedProblemId]);

  const selectedProblem = useMemo(
    () => problems.find((problem) => problem.id === selectedProblemId) || null,
    [problems, selectedProblemId]
  );

  const currentCode = selectedProblem
    ? codeByProblem[selectedProblem.id] ?? DEFAULT_TEMPLATE
    : DEFAULT_TEMPLATE;

  const updateCode = (value) => {
    if (!selectedProblem) return;
    setCodeByProblem((prev) => ({
      ...prev,
      [selectedProblem.id]: value ?? ''
    }));
  };

  const ensureTemplate = (problemId) => {
    setCodeByProblem((prev) => {
      if (prev[problemId]) return prev;
      return {
        ...prev,
        [problemId]: DEFAULT_TEMPLATE
      };
    });
  };

  const handleSelectProblem = (problemId) => {
    setSelectedProblemId(problemId);
    ensureTemplate(problemId);
    setResult(null);
  };

  const handleSubmit = async () => {
    if (!selectedProblem || !currentCode.trim()) return;

    try {
      setSubmitting(true);
      setError('');
      const response = await codingAPI.submit({
        problem_id: selectedProblem.id,
        code: currentCode,
        language
      });
      setResult(response?.data || null);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Code submission failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loadingProblems) {
    return (
      <section className={styles.loadingState}>
        <Loader2 className={styles.spinner} size={22} />
        <p>Loading coding problems...</p>
      </section>
    );
  }

  return (
    <section className={styles.page}>
      {error ? <div className={styles.errorBanner}>{error}</div> : null}

      <div className={styles.splitLayout}>
        <aside className={styles.problemPanel}>
          <h2>Problem List</h2>
          <div className={styles.problemList}>
            {problems.map((problem) => (
              <button
                key={problem.id}
                type="button"
                className={`${styles.problemItem} ${selectedProblemId === problem.id ? styles.problemItemActive : ''}`}
                onClick={() => handleSelectProblem(problem.id)}
              >
                <div className={styles.problemTitleRow}>
                  <span className={styles.problemTitle}>{problem.title}</span>
                  <span className={`${styles.badge} ${difficultyClassMap[problem.difficulty] || styles.badgeMedium}`}>
                    {problem.difficulty}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </aside>

        <main className={styles.mainPanel}>
          {!selectedProblem ? (
            <div className={styles.emptyState}>
              <p>Select a problem to begin coding.</p>
            </div>
          ) : (
            <>
              <article className={styles.problemDetails}>
                <div className={styles.detailsHeader}>
                  <h1>{selectedProblem.title}</h1>
                  <span className={`${styles.badge} ${difficultyClassMap[selectedProblem.difficulty] || styles.badgeMedium}`}>
                    {selectedProblem.difficulty}
                  </span>
                </div>
                <p className={styles.description}>{selectedProblem.description}</p>

                {selectedProblem.examples?.length ? (
                  <div className={styles.examplesSection}>
                    <h3>Examples</h3>
                    {selectedProblem.examples.map((item, index) => (
                      <div key={`${selectedProblem.id}-ex-${index}`} className={styles.exampleCard}>
                        <p><strong>Input:</strong> {item.input}</p>
                        <p><strong>Output:</strong> {item.output}</p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>

              <article className={styles.editorCard}>
                <Editor
                  height="48vh"
                  language={language}
                  theme="vs-dark"
                  value={currentCode}
                  onChange={updateCode}
                  onMount={(editor) => {
                    editorRef.current = editor;
                  }}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    smoothScrolling: true,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    padding: { top: 14 }
                  }}
                />
              </article>

              <div className={styles.actionsRow}>
                <select
                  className={styles.languageSelect}
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                </select>

                <div className={styles.actionButtons}>
                  <button
                    type="button"
                    className={styles.secondaryButton}
                    disabled={!currentCode.trim() || submitting}
                    onClick={handleSubmit}
                  >
                    Run Code
                  </button>
                  <button
                    type="button"
                    className={styles.primaryButton}
                    disabled={!currentCode.trim() || submitting}
                    onClick={handleSubmit}
                  >
                    {submitting ? 'Submitting...' : 'Submit'}
                  </button>
                </div>
              </div>

              {result ? (
                <article className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <span className={`${styles.resultBadge} ${result.passed ? styles.resultPassed : styles.resultFailed}`}>
                      {result.passed ? 'Passed' : 'Failed'}
                    </span>
                    <span className={styles.execTime}>Execution Time: {result.execution_time || '-'}</span>
                  </div>

                  <div className={styles.tableWrap}>
                    <table className={styles.resultTable}>
                      <thead>
                        <tr>
                          <th>Input</th>
                          <th>Expected</th>
                          <th>Actual</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(result.test_results || []).map((test, index) => (
                          <tr
                            key={`test-${index}`}
                            className={test.status === 'passed' ? styles.rowPassed : styles.rowFailed}
                          >
                            <td>{test.input}</td>
                            <td>{test.expected}</td>
                            <td>{test.actual}</td>
                            <td>
                              <span className={`${styles.statusPill} ${resultClassMap[test.status] || styles.statusFailed}`}>
                                {test.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </article>
              ) : null}
            </>
          )}
        </main>
      </div>
    </section>
  );
};

export default CodingPracticePage;
