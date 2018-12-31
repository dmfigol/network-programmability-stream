package main

import (
    "fmt"
    "time"
    "math/rand"
    "math"
)

var c, python, java bool = false, true, false
const C = 5

func add(x int, y int) int {
    return x + y
}

func swap(x string, y string) (string, string) {
    return y, x
}

func main() {
    i := -1
    var j int8 = 13
    rand.Seed(time.Now().UnixNano())

    curTime := time.Now()
    fmt.Printf("hello, stream!\n")
    fmt.Println("Cisco Live Barcelona is soon and I have to finish my presentation deck.")

    fmt.Println("The time is", curTime, "in unix nanoseconds:", curTime.UnixNano())

    fmt.Println("Selected number:", rand.Intn(10))

    fmt.Printf("Now you have %f problems.\n", math.Sqrt(7))

    fmt.Println(math.Pi)
    a, b := swap("sad", "happy")
    fmt.Println(a, b)
    fmt.Println(i, c, python, java)
    fmt.Println(j)

    sum := 0
    for i := 0; i < 10; i++ {
        if i % 2 == 0 {
            sum += i
        }
    }
    fmt.Println(sum)
}
