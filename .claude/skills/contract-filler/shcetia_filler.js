/**
 * shcetia 合同基本信息维护 - 自动填充脚本
 * 用法：
 *   1. 把 contract_filler_ocr.py 生成的 JSON 复制到 contractData 变量
 *   2. 在 F12 控制台粘贴本脚本全部内容
 *   3. 按回车执行
 */

// ===== 第1步：把 OCR 识别的数据贴到这里 =====
var contractData = {
  "报建编号": "",
  "工程地址": "",
  "设计单位": "",
  "见证单位": "",
  "施工单位": ""
};

// 如果你已经复制了 JSON 到剪贴板，用下面这行自动解析（IE不支持，需手动贴）
// var contractData = JSON.parse(prompt('把 OCR 生成的 JSON 粘贴到这里：'));

// ===== 第2步：填充函数 =====
function fillForm() {
  var logs = [];
  function log(msg) { logs.push(msg); console.log(msg); }

  // --- 1. 报建编号 ---
  var reportNumInput = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_BuildingReportNumberSearch');
  if (reportNumInput && contractData['报建编号']) {
    reportNumInput.value = contractData['报建编号'];
    log('[OK] 报建编号已填: ' + contractData['报建编号']);

    // 触发 onchange（如果存在）
    if (reportNumInput.onchange) {
      reportNumInput.onchange();
      log('[OK] 已触发报建编号 onchange');
    }

    // 点击"根据报建编号获得"按钮
    var searchBtn = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_searchProj');
    if (searchBtn) {
      // 延迟一点等 onchange 先跑完
      setTimeout(function() {
        searchBtn.click();
        log('[OK] 已点击"根据报建编号获得"');
      }, 300);
    }
  } else {
    log('[X] 报建编号: 未找到输入框或数据为空');
  }

  // --- 2. 工程地址 ---
  var addressInput = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_ProjectAddress');
  if (addressInput && contractData['工程地址']) {
    addressInput.value = contractData['工程地址'];
    log('[OK] 工程地址已填: ' + contractData['工程地址'].substring(0, 30) + '...');
  } else {
    log('[X] 工程地址: 未找到输入框或数据为空');
  }

  // --- 3. 设计单位（下拉匹配）---
  var designSelect = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_SelectDesignUnitName');
  if (designSelect && contractData['设计单位']) {
    var target = contractData['设计单位'];
    var matched = false;
    var bestMatchIndex = -1;
    var bestMatchScore = 0;

    for (var i = 0; i < designSelect.options.length; i++) {
      var optText = designSelect.options[i].text;
      // 完全匹配
      if (optText === target) {
        designSelect.selectedIndex = i;
        matched = true;
        log('[OK] 设计单位完全匹配: ' + optText);
        break;
      }
      // 包含匹配（选项包含目标 或 目标包含选项）
      if (optText.indexOf(target) >= 0 || target.indexOf(optText) >= 0) {
        var score = Math.min(optText.length, target.length);
        if (score > bestMatchScore) {
          bestMatchScore = score;
          bestMatchIndex = i;
        }
      }
    }

    if (!matched && bestMatchIndex >= 0) {
      designSelect.selectedIndex = bestMatchIndex;
      matched = true;
      log('[OK] 设计单位模糊匹配: ' + designSelect.options[bestMatchIndex].text);
    }

    if (matched && designSelect.onchange) {
      designSelect.onchange();
      log('[OK] 已触发设计单位 onchange');
    }

    if (!matched) {
      log('[!] 设计单位未匹配，请手动选择。目标: ' + target);
      // 把目标名字写到剪贴板方便粘贴
      window.clipboardData && window.clipboardData.setData('Text', target);
      log('[提示] 设计单位名称已复制到剪贴板');
    }
  } else {
    log('[X] 设计单位: 未找到下拉框或数据为空');
  }

  // --- 4. 见证单位（复制到剪贴板 + 提示手动）---
  var witnessSelect = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_SelectSuperviseUnitName');
  if (witnessSelect && contractData['见证单位']) {
    var wTarget = contractData['见证单位'];
    var wMatched = false;
    for (var j = 0; j < witnessSelect.options.length; j++) {
      if (witnessSelect.options[j].text.indexOf(wTarget) >= 0 || wTarget.indexOf(witnessSelect.options[j].text) >= 0) {
        witnessSelect.selectedIndex = j;
        wMatched = true;
        log('[OK] 见证单位匹配: ' + witnessSelect.options[j].text);
        if (witnessSelect.onchange) witnessSelect.onchange();
        break;
      }
    }
    if (!wMatched) {
      window.clipboardData && window.clipboardData.setData('Text', wTarget);
      log('[!] 见证单位未匹配，名称已复制到剪贴板，请手动点击"编辑"按钮粘贴选择');
    }
  }

  // --- 5. 施工单位（复制到剪贴板 + 提示手动）---
  var buildSelect = document.getElementById('ctl00_cphMain_BasicInfo1_fvBasicInfo_SelectBuildUnitName');
  if (buildSelect && contractData['施工单位']) {
    var bTarget = contractData['施工单位'];
    var bMatched = false;
    for (var k = 0; k < buildSelect.options.length; k++) {
      if (buildSelect.options[k].text.indexOf(bTarget) >= 0 || bTarget.indexOf(buildSelect.options[k].text) >= 0) {
        buildSelect.selectedIndex = k;
        bMatched = true;
        log('[OK] 施工单位匹配: ' + buildSelect.options[k].text);
        if (buildSelect.onchange) buildSelect.onchange();
        break;
      }
    }
    if (!bMatched) {
      window.clipboardData && window.clipboardData.setData('Text', bTarget);
      log('[!] 施工单位未匹配，名称已复制到剪贴板，请手动点击"编辑"按钮粘贴选择');
    }
  }

  // --- 汇总 ---
  log('\n========== 填充完成 ==========');
  alert('填充完成！\n\n' + logs.join('\n'));
}

// ===== 第3步：执行 =====
fillForm();
