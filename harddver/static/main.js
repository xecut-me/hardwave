const digits = [...document.querySelectorAll(".clock-digit")];
const positions = [8, 9, 5, 6, 0, 1, 2, 3, 11, 12, 14, 15, 17, 18, 20, 21, 22];
const offset = new Date().getTimezoneOffset() * 60000;
let lastTime = "";

function renderTimer() {
    const time = new Date(Date.now() - offset).toISOString();

    for (let i = 0; i < positions.length; i++) {
        const d = positions[i];

        if (lastTime[d] != time[d]) {
            digits[i].style.backgroundPosition = `-${+time[d] * 68}px 0`;
        }
    }

    lastTime = time;
    requestAnimationFrame(renderTimer);
}

async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const videoElement = document.querySelector(".camera");
    videoElement.srcObject = stream;
}

async function onData(paramsJson) {
    const params = JSON.parse(paramsJson);

    if ("temp" in params) {
        document.querySelector(".widget-temperature").innerText = params.temp + " " + params.w;
    }

    if ("co2" in params) {
        document.querySelector(".widget-co2").innerText = params.co2;
    }

    if ("devices" in params) {
        document.querySelector(".widget-devices").innerText = "devices: " + params.devices;
    }

    if ("ai_token" in params) {
        document.querySelector(".ai-token").src = params.ai_token;
    }

    if ("username" in params) {
        const div = document.createElement("div");
        div.innerText = `@${params.username}: ${params.text}\n`;

        const widgetChat = document.querySelector(".widget-chat");
        widgetChat.appendChild(div);
        widgetChat.scrollTop = widgetChat.scrollHeight;
    }
}

const dvdWidth = 1080 - 350, dvdHeight = 1920 - 158, dvd = document.querySelector(".widget-dvd");
let dvdLastRenderTime = Date.now(), dx = 0.3, dy = 0.3;
let x = Math.floor(Math.random() * dvdWidth), y = Math.floor(Math.random() * dvdHeight);
let dvdHue = 0;

function setDvdRandomColor() {
    const hueHalfGuard = 30;

    dvdHue = (dvdHue + hueHalfGuard + Math.random() * (360 - 2 * hueHalfGuard)) % 360;

    document.querySelector("#dvd").setAttribute("fill", `hsl(${dvdHue}, 100%, 50%)`);
}

function animateDvd() {
    let renderTime = Date.now();

    x += dx * (renderTime - dvdLastRenderTime);
    y += dy * (renderTime - dvdLastRenderTime);

    if (x > dvdHeight) { x = 2 * dvdHeight - x; dx *= -1; setDvdRandomColor(); }
    if (x < 0) { x = - x; dx *= -1; setDvdRandomColor(); }

    if (y > dvdWidth) { y = 2 * dvdWidth - y; dy *= -1; setDvdRandomColor(); }
    if (y < 0) { y = - y; dy *= -1; setDvdRandomColor(); }

    dvdLastRenderTime = renderTime;

    dvd.style.top = x + "px";
    dvd.style.left = y + "px";
    requestAnimationFrame(animateDvd);
}

renderTimer();
animateDvd();
startCamera();

if (location.toString().includes("debug")) {
    onData(JSON.stringify({
        co2: "0.238 kg of CO₂ emitted so far",
        w: "3.26W",
        temp: "+63.0°C",
        devices: 1
    }));

    for (let i = 0; i < 10; i++) {
        onMessage(JSON.stringify({ username: "testuser", text: "test message " + i }));
    }

    [...document.querySelectorAll(".widget")].forEach(e => e.style.border = "3px white solid");

    document.querySelector(".screen").style.animation = "unset";
}
