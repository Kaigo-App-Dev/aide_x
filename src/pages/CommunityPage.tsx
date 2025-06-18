import React from 'react';

const CommunityPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h2 className="text-3xl font-bold text-gray-900 mb-8">コミュニティ機能</h2>
      
      {/* 概要セクション */}
      <section className="mb-12">
        <h3 className="text-2xl font-semibold text-gray-800 mb-4">概要</h3>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">概要</label>
            <p className="text-gray-600">他のユーザーとの交流を促進。</p>
          </div>
        </div>
      </section>

      {/* 要素セクション */}
      <section className="mb-12">
        <h3 className="text-2xl font-semibold text-gray-800 mb-4">要素</h3>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">要素</label>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>グループチャット</li>
              <li>体操チャレンジの共有</li>
              <li>友達招待機能</li>
              <li>フォーラムでの質問と回答</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
};

export default CommunityPage; 