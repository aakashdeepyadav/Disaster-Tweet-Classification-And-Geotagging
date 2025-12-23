import React from 'react';

function SkeletonLoader({ type = 'card', count = 1 }) {
  const SkeletonCard = () => (
    <div className="card" style={{ 
      animation: 'pulse 1.5s ease-in-out infinite',
      pointerEvents: 'none'
    }}>
      <div className="card-header">
        <div style={{
          height: '24px',
          width: '60%',
          background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 25%, rgba(99, 102, 241, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%)',
          backgroundSize: '200% 100%',
          borderRadius: '4px',
          marginBottom: '8px',
          animation: 'shimmer 1.5s infinite'
        }}></div>
        <div style={{
          height: '16px',
          width: '40%',
          background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 25%, rgba(99, 102, 241, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%)',
          backgroundSize: '200% 100%',
          borderRadius: '4px',
          animation: 'shimmer 1.5s infinite'
        }}></div>
      </div>
      <div style={{ padding: '16px' }}>
        {[1, 2, 3].map((i) => (
          <div key={i} style={{ marginBottom: '16px' }}>
            <div style={{
              height: '12px',
              width: '30%',
              background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 25%, rgba(99, 102, 241, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%)',
              backgroundSize: '200% 100%',
              borderRadius: '4px',
              marginBottom: '8px',
              animation: 'shimmer 1.5s infinite'
            }}></div>
            <div style={{
              height: '60px',
              width: '100%',
              background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 25%, rgba(99, 102, 241, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%)',
              backgroundSize: '200% 100%',
              borderRadius: '8px',
              animation: 'shimmer 1.5s infinite'
            }}></div>
          </div>
        ))}
      </div>
    </div>
  );

  const SkeletonButton = () => (
    <div style={{
      height: '48px',
      width: '100%',
      background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.1) 25%, rgba(99, 102, 241, 0.2) 50%, rgba(99, 102, 241, 0.1) 75%)',
      backgroundSize: '200% 100%',
      borderRadius: '12px',
      animation: 'shimmer 1.5s infinite',
      marginTop: '16px'
    }}></div>
  );

  if (type === 'button') {
    return <SkeletonButton />;
  }

  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <SkeletonCard key={idx} />
      ))}
    </>
  );
}

export default SkeletonLoader;



