browser.contextMenus.create(
  {
    id: "poney-hot-summarize",
    title: "Summarize this!",
    contexts: ["link", "selection"]
  }
);

browser.contextMenus.create(
  {
    id: "poney-hot-factcheck",
    title: "Check this!",
    contexts: ["selection"]
  }
);



browser.contextMenus.onClicked.addListener((info, tab) => {
  browser.storage.local.get('backendDomain').then(result => {
    const backendDomain = result.backendDomain || "http://localhost.de:8080";
    const backendUrl = `${backendDomain}/processor`;

    console.log("Backend URL:", backendUrl);  
    
    try {
      if (info.menuItemId === "poney-hot-summarize" && info.linkUrl) {
      
      console.log("Sending URL to backend:", info.linkUrl);
      browser.tabs.sendMessage(tab.id, {
        action: "showModal",
        content: "Please wait..."
      });
      fetch(backendUrl, {
        method: "POST",
        headers: {
        "Content-Type": "application/json"
        },
        body: JSON.stringify({ input_text: '!!!' + info.linkUrl, return_html: true })
      })
      .then(response => {
        if (!response.ok) {
        throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        console.log("URL sent to backend successfully:", data);
        if (data.response) {
        browser.tabs.sendMessage(tab.id, {
          action: "showModal",
          content: data.response
        });
        }
      })
      .catch(error => {
        console.error("Failed to send URL to backend:", error);
      });
      } else if (info.menuItemId === "poney-hot-factcheck" && info.selectionText) {
      
      console.log("Sending text to backend:", info.selectionText);
      browser.tabs.sendMessage(tab.id, {
        action: "showModal",
        content: "Please wait..."
      });
      fetch(backendUrl, {
        method: "POST",
        headers: {
        "Content-Type": "application/json"
        },
        body: JSON.stringify({ input_text: '???' + info.selectionText, return_html: true })
      })
      .then(response => {
        if (!response.ok) {
        throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        console.log("URL sent to backend successfully:", data);
        if (data.response) {
        browser.tabs.sendMessage(tab.id, {
          action: "showModal",
          content: data.response
        });
        }
      })
      .catch(error => {
        console.error("Failed to send URL to backend:", error);
      });

      } else {

      console.error("Unsupported context menu item:", info);

      }
    } catch (error) {
      console.error("An error occurred:", error);
    }



  });
});