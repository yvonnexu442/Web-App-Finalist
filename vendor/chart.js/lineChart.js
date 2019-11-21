var ctxL = document.getElementById("lineChart").getContext('2d');
    var gradientFill = ctxL.createLinearGradient(0, 0, 0, 290);
    gradientFill.addColorStop(0, "rgba(173, 53, 186, 1)");
    gradientFill.addColorStop(1, "rgba(173, 53, 186, 0.1)");
    var myLineChart = new Chart(ctxL, {
      type: 'line',
      data: {
        labels: ["January", "February", "March", "April", "May", "June", "July"],
        datasets: [
          {
            label: "My First dataset",
            data: [0, 65, 45, 65, 35, 65, 0],
            backgroundColor: gradientFill,
            borderColor: [
              '#AD35BA',
            ],
            borderWidth: 2,
            pointBorderColor: "#fff",
            pointBackgroundColor: "rgba(173, 53, 186, 0.1)",
          }
        ]
      },
      options: {
        responsive: true
      }
    });