package main

import (
	"bufio"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
	"time"

	"github.com/howeyc/gopass"
	"golang.org/x/crypto/ssh"
)

// go-lint go away, ty
type Device struct {
	host     string
	hostname string
}

// type DeviceResult struct {
// 	device Device
// 	result string
// }

const COMMANDS string = "show version; show ip int brief; show arp; show ip route; show plat software status control-processor brief; show platform resources"

func timeTrack(start time.Time, name string) {
	elapsed := time.Since(start)
	log.Printf("%s took %s", name, elapsed)
}

func readHosts(hostFile string) []Device {
	var devices []Device
	file, err := os.Open(hostFile)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		hostData := strings.Fields(line)
		device := Device{hostData[0], hostData[1]}
		devices = append(devices, device)
	}
	return devices
}

func executeCmd(device Device, commands []string, config *ssh.ClientConfig) *[]string {
	// Need pseudo terminal if we want to have an SSH session
	// similar to what you have when you use a SSH client
	modes := ssh.TerminalModes{
		ssh.ECHO:          0,     // disable echoing
		ssh.TTY_OP_ISPEED: 14400, // input speed = 14.4kbaud
		ssh.TTY_OP_OSPEED: 14400, // output speed = 14.4kbaud
	}
	conn, err := ssh.Dial("tcp", device.host+":22", config)
	if err != nil {
		log.Println(err)
		return &[]string{1: device.host}
	}
	session, err := conn.NewSession()
	if err != nil {
		log.Fatal(err)
	}
	// You can use session.Run() here but that only works
	// if you need a run a single command or you commands
	// are independent of each other.
	err = session.RequestPty("xterm", 80, 40, modes)
	if err != nil {
		log.Fatalf("request for pseudo terminal failed: %s", err)
	}
	stdBuf, err := session.StdoutPipe()
	if err != nil {
		log.Fatalf("request for stdout pipe failed: %s", err)
	}
	stdinBuf, err := session.StdinPipe()
	if err != nil {
		log.Fatalf("request for stdin pipe failed: %s", err)
	}
	err = session.Shell()
	if err != nil {
		log.Fatalf("failed to start shell: %s", err)
	}

	for _, command := range commands {
		stdinBuf.Write([]byte(command + "\n"))
	}
	result := make([]string, 0)
	return readStdBuf(stdBuf, &result, device)
}

func readStdBuf(stdBuf io.Reader, result *[]string, device Device) *[]string {
	stdoutBuf := make([]byte, 1000000)
	time.Sleep(time.Millisecond * 100)
	byteCount, err := stdBuf.Read(stdoutBuf)
	if err != nil {
		log.Fatal(err)
	}
	//fmt.Println("Bytes received: ", byteCount)
	s := string(stdoutBuf[:byteCount])
	lines := strings.Split(s, "\n")
	//fmt.Println("====", lines[len(lines)-1], "====")

	if strings.TrimSpace(lines[len(lines)-1]) != device.hostname+"#" {
		*result = append(*result, lines...)
		readStdBuf(stdBuf, result, device)
		return result
	}
	//fmt.Println("end reached")
	*result = append(*result, lines...)
	return result
}

func inputPassword() string {
	fmt.Printf("Password: ")
	getPass, _ := gopass.GetPasswdMasked()
	passwd := string(getPass[:])

	if len(passwd) == 0 {
		log.Fatal("no password entered")
	}

	return passwd
}

func main() {
	defer timeTrack(time.Now(), "collecting outputs")
	fmt.Println("Usage: command hosts file username")
	if len(os.Args) <= 1 {
		os.Exit(1)
	}
	devices := readHosts(os.Args[1])
	var (
		User       string
		commands   = strings.Split(COMMANDS, "; ")
		outStrings []string
	)
	User = os.Args[2]
	passwd := inputPassword()
	results := make(chan *[]string, 100) // TODO: review
	config := &ssh.ClientConfig{
		User:            User,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Auth: []ssh.AuthMethod{
			ssh.Password(passwd),
		},
	}
	for _, device := range devices {
		go func(device Device) {
			results <- executeCmd(device, commands, config)
		}(device) // TODO: how to distinguish results for different hosts?
	}
	for i := 0; i < len(devices); i++ {
		result := <-results
		outStrings = append(outStrings, *result...)
	}
	for _, line := range outStrings {
		fmt.Println(line)
	}
}