const config = {}
const context = {}
const lineChart = {}
const source = new EventSource("/chart-data");
$(document).ready(function () {
    openFirstTab();
    var canvasElements = document.getElementsByClassName("graph");
    setConfig(canvasElements);
    updateChart(canvasElements);
});

function updateChart(canvasElements) {
    source.onmessage = function (event) {
        const data = JSON.parse(event.data);
        for (var i = 0; i < canvasElements.length; i++) {
            appareil = canvasElements[i].id;
            if (data[appareil].time != "" && data[appareil].value != "") {
                if (config[appareil].data.labels.length === 100) {
                    config[appareil].data.labels.shift();
                    config[appareil].data.datasets[0].data.shift();
                    config[appareil].data.datasets[0].borderColor.shift();
                    config[appareil].data.datasets[0].backgroundColor.shift();
                }

                config[appareil].data.labels.push(data[appareil].time);
                config[appareil].data.datasets[0].data.push(data[appareil].value);

                if (data[appareil].anomaly === 'false') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(54, 240, 92)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(54, 240, 92)');
                }
                else if (data[appareil].anomaly === 'true') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(255, 99, 132)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(255, 99, 132)');
                    //affiche une alerte dans historique
                    value=config[appareil].data.datasets[0].data[0];
                    showAlert(appareil,value);
                }
                else if (data[appareil].anomaly === 'null') {
                    config[appareil].data.datasets[0].backgroundColor.push('rgb(0, 0, 0)');
                    config[appareil].data.datasets[0].borderColor.push('rgb(0, 0, 0)');
                }

                lineChart[appareil].update();
            }
        }
    };
}

function setConfig(canvasElements) {
    for (var i = 0; i < canvasElements.length; i++) {
        appareil = canvasElements[i].id;
        config[appareil] = {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: "",
                    backgroundColor: [],
                    borderColor: [],
                    data: [],
                    fill: false,
                }],
            },
            options: {
                responsive: true,
                title: {
                    display: true,
                    text: `Relevé du capteur ${appareil}`,
                },
                tooltips: {
                    mode: 'index',
                    intersect: false,
                },
                hover: {
                    mode: 'nearest',
                    intersect: true
                },
                legend: {
                    display: false,
                },
                scales: {
                    xAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Time',
                        }
                    }],
                    yAxes: [{
                        display: true,
                        scaleLabel: {
                            display: true,
                            labelString: 'Value',
                        }
                    }]
                }
            }
        };

        context[appareil] = document.getElementById(appareil).getContext('2d');

        lineChart[appareil] = new Chart(context[appareil], config[appareil]);

    }
}

function check(appareil) {
    var thisCheckbox = document.getElementById(appareil.id);
    var container = document.getElementById(`container-${appareil.id.split("-")[1]}`)
    if (thisCheckbox.checked) {
        container.style.display = "block";
    } else {
        container.style.display = "none";
    }
}

function openFirstTab() {
    var tabcontent;
    var navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    navitem = document.getElementsByClassName("nav-item");

    tabcontent[0].style.display = "block";
    navitem[0].className += " active";
}


function openTab(evt, id) {
    var i, tabcontent, navitem;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    navitem = document.getElementsByClassName("nav-item");
    for (i = 0; i < navitem.length; i++) {
        navitem[i].className = navitem[i].className.replace(" active", "");
    }
    document.getElementById("tab-"+id).style.display = "block";
    evt.currentTarget.className += " active";
}

function showAlert(appareil,value){
    //alert(`Anomalies : ${appareil} values ${value}`);
}