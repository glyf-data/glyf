import React, {useState} from 'react';
import Link from '@docusaurus/Link';
import ThemedImage from '@theme/ThemedImage';
import useBaseUrl from '@docusaurus/useBaseUrl';

// One chart type as a card: the chart as the product demo draws it, and the
// .ggsql file that drew it one click away. The code is the card's children, a
// fenced block, so the docs test can compare it against the shipped file.
export default function ChartTypeCard({type, title, summary, anchor, children}) {
  const [view, setView] = useState('chart');
  const light = useBaseUrl(`/img/chart-types/${type}-light.webp`);
  const dark = useBaseUrl(`/img/chart-types/${type}-dark.webp`);
  return (
    <article className="chartTypeCard">
      <header className="chartTypeCard__head">
        <div>
          <h3 className="chartTypeCard__title">{title}</h3>
          <code className="chartTypeCard__draw">DRAW {type}</code>
        </div>
        <div className="chartTypeCard__switch" role="group" aria-label={`${title}: chart or code`}>
          {['chart', 'code'].map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={view === option}
              className={view === option ? 'is-on' : undefined}
              onClick={() => setView(option)}>
              {option === 'chart' ? 'Chart' : 'Code'}
            </button>
          ))}
        </div>
      </header>
      <div className={`chartTypeCard__body chartTypeCard__body--${view}`}>
        {view === 'chart' ? (
          <ThemedImage
            className="chartTypeCard__image"
            alt={`A ${type} chart from the product analytics example`}
            sources={{light, dark}}
            loading="lazy"
            title="Open full size"
            onClick={(event) => window.open(event.currentTarget.currentSrc || event.currentTarget.src, '_blank', 'noopener')}
          />
        ) : (
          <div className="chartTypeCard__code">{children}</div>
        )}
      </div>
      <footer className="chartTypeCard__foot">
        <p>{summary}</p>
        {anchor && <Link to={`#${anchor}`}>How it reads →</Link>}
      </footer>
    </article>
  );
}
