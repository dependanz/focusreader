"use strict";

const BADGE_COLOR = "#C65F3C";

async function updateBadge(tabId, enabled) {
  if (!Number.isInteger(tabId)) {
    return;
  }

  await chrome.action.setBadgeBackgroundColor({
    tabId,
    color: BADGE_COLOR
  });
  await chrome.action.setBadgeText({
    tabId,
    text: enabled ? "ON" : ""
  });
}

async function toggleTab(tabId) {
  if (!Number.isInteger(tabId)) {
    return;
  }

  try {
    const state = await chrome.tabs.sendMessage(tabId, {
      type: "focusreader:toggle"
    });
    await updateBadge(tabId, Boolean(state && state.enabled));
  } catch (_error) {
    await updateBadge(tabId, false);
  }
}

chrome.commands.onCommand.addListener(async function handleCommand(command) {
  if (command !== "toggle-focusreader") {
    return;
  }

  const tabs = await chrome.tabs.query({
    active: true,
    currentWindow: true
  });
  await toggleTab(tabs[0] && tabs[0].id);
});

chrome.runtime.onMessage.addListener(function handleRuntimeMessage(
  message,
  sender
) {
  if (message && message.type === "focusreader:state-changed") {
    updateBadge(sender.tab && sender.tab.id, Boolean(message.enabled)).catch(
      function ignoreClosedTab() {}
    );
  }
});

chrome.tabs.onUpdated.addListener(function handleTabUpdate(tabId, changeInfo) {
  if (changeInfo.status === "loading") {
    updateBadge(tabId, false).catch(function ignoreClosedTab() {});
  }
});

