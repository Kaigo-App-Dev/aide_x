// edit_structure.js

function saveStructureAjax(structureId) {
  const data = {
    title: document.getElementById("title").value,
    description: document.getElementById("description").value,
    project: document.getElementById("project").value,
    content: document.getElementById("content").value,
    is_final: document.getElementById("is_final")?.checked || false
  };

  console.log("送信データ:", data);

  fetch(`/structure/ajax_save/${structureId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  }).then(res => res.json())
    .then(result => {
      if (result.success) {
         if (result.evaluation) {
          document.getElementById("evaluation-area").innerHTML = `
            <h3>✅ 構成評価（AI）</h3>
            <ul>
              <li><strong>Intent一致度:</strong> ${result.evaluation.intent_match} / 100</li>
              <li><strong>品質スコア:</strong> ${result.evaluation.quality_score} / 100</li>
              <li><strong>評価理由:</strong> ${result.evaluation.intent_reason}</li>
            </ul>
          `;
        }

        if (result.ui_html) {
          document.getElementById("ui-area").innerHTML = result.ui_html;
        }

        if (result.diff_html) {
          document.getElementById("diff-area").innerHTML = result.diff_html;
        }

        if (result.logs_html) {
          document.getElementById("logs-area").innerHTML = result.logs_html;
        }

        // 🔔 ⑧ 成功通知 & スクロール
        alert("保存・評価・UI構成を更新しました");
        document.getElementById("evaluation-area").scrollIntoView({ behavior: "smooth" });
      } else {
        alert("保存に失敗しました: " + result.message);
      }
    })
    .catch(err => {
      console.error(err);
      alert("通信エラーが発生しました");
    });
}
