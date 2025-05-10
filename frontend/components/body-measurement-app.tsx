"use client"

import { useState, useEffect } from "react"
import {
  Camera,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Download,
  FileText,
  FileJson,
  FileSpreadsheetIcon as FileCsv,
  ChevronDown,
  History,
  LineChart,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

export default function BodyMeasurementApp() {
  const [isRecording, setIsRecording] = useState(false)
  const [measurements, setMeasurements] = useState({
    height: 175,
    shoulderWidth: 45.2,
    chest: 98.6,
    waist: 82.3,
    hips: 94.1,
    inseam: 81.5,
  })

  const [history, setHistory] = useState([
    { date: "2024-05-01", height: 175, shoulderWidth: 45.0, chest: 99.1, waist: 83.2, hips: 94.5, inseam: 81.5 },
    { date: "2024-04-15", height: 175, shoulderWidth: 45.2, chest: 99.8, waist: 84.1, hips: 95.0, inseam: 81.5 },
    { date: "2024-03-30", height: 175, shoulderWidth: 45.2, chest: 100.3, waist: 85.7, hips: 95.8, inseam: 81.5 },
  ])

  // Simulate measurement updates when recording
  useEffect(() => {
    let interval: NodeJS.Timeout

    if (isRecording) {
      interval = setInterval(() => {
        setMeasurements((prev) => ({
          ...prev,
          shoulderWidth: +(prev.shoulderWidth + (Math.random() * 0.2 - 0.1)).toFixed(1),
          chest: +(prev.chest + (Math.random() * 0.4 - 0.2)).toFixed(1),
          waist: +(prev.waist + (Math.random() * 0.4 - 0.2)).toFixed(1),
          hips: +(prev.hips + (Math.random() * 0.3 - 0.15)).toFixed(1),
        }))
      }, 2000)
    }

    return () => clearInterval(interval)
  }, [isRecording])

  const handleCaptureMeasurement = () => {
    const newMeasurement = {
      date: new Date().toISOString().split("T")[0],
      ...measurements,
    }

    setHistory((prev) => [newMeasurement, ...prev])
  }

  return (
    <div className="flex flex-col min-h-screen">
      {/* Navigation Bar */}
      <header className="border-b bg-white">
        <div className="container flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Camera className="h-6 w-6 text-blue-600" />
            <h1 className="text-xl font-semibold">BodyMetrics Pro</h1>
          </div>

          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
              <span className="sr-only">Settings</span>
            </Button>

            <div className="flex items-center gap-2">
              <Avatar>
                <AvatarImage src="/placeholder.svg" alt="User" />
                <AvatarFallback>JD</AvatarFallback>
              </Avatar>
              <div className="hidden md:block">
                <p className="text-sm font-medium">John Doe</p>
                <p className="text-xs text-muted-foreground">Premium Plan</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container flex flex-1 flex-col lg:flex-row gap-6 p-4 md:p-6">
        {/* Left Column - Video Feed (60%) */}
        <div className="w-full lg:w-3/5 flex flex-col gap-4">
          <Card className="flex-1">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-center">
                <CardTitle>Camera Feed</CardTitle>
                <Badge variant={isRecording ? "destructive" : "outline"}>{isRecording ? "Recording" : "Ready"}</Badge>
              </div>
              <CardDescription>Position yourself in the center of the frame</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 p-0 relative">
              <div className="relative aspect-video w-full bg-black rounded-md overflow-hidden">
                {/* Placeholder for camera feed */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-white text-center">
                    <Camera className="h-16 w-16 mx-auto mb-2 opacity-20" />
                    <p className="text-sm opacity-50">Camera feed will appear here</p>
                    {!isRecording && (
                      <Button className="mt-4 bg-blue-600 hover:bg-blue-700" onClick={() => setIsRecording(true)}>
                        Start Camera
                      </Button>
                    )}
                  </div>
                </div>

                {/* Measurement guides overlay */}
                {isRecording && (
                  <div className="absolute inset-0">
                    <div className="absolute left-1/2 top-0 bottom-0 w-px bg-blue-500/30"></div>
                    <div className="absolute top-1/2 left-0 right-0 h-px bg-blue-500/30"></div>
                    <div className="absolute top-[30%] left-0 right-0 h-px bg-blue-500/20 border-dashed"></div>
                    <div className="absolute top-[70%] left-0 right-0 h-px bg-blue-500/20 border-dashed"></div>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2 pt-2">
              <Button
                variant={isRecording ? "destructive" : "default"}
                className={!isRecording ? "bg-blue-600 hover:bg-blue-700" : ""}
                onClick={() => setIsRecording(!isRecording)}
              >
                {isRecording ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
                {isRecording ? "Pause" : "Start"} Recording
              </Button>

              <Button variant="outline" onClick={() => setIsRecording(false)}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Reset
              </Button>

              <Button variant="secondary" className="ml-auto" onClick={handleCaptureMeasurement}>
                Capture Measurements
              </Button>
            </CardFooter>
          </Card>

          {/* Measurement Controls */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Measurement Controls</CardTitle>
              <CardDescription>Adjust settings for accurate measurements</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Measurement Units</label>
                  <div className="flex">
                    <Button variant="outline" className="rounded-r-none bg-blue-50 border-blue-600 text-blue-600">
                      cm
                    </Button>
                    <Button variant="outline" className="rounded-l-none">
                      inches
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Calibration</label>
                  <Button variant="outline" className="w-full">
                    Calibrate Camera
                  </Button>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Detection Sensitivity</label>
                  <div className="flex items-center gap-4">
                    <span className="text-xs">Low</span>
                    <Progress value={75} className="flex-1" />
                    <span className="text-xs">High</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Measurement Mode</label>
                  <div className="flex">
                    <Button variant="outline" className="rounded-r-none bg-blue-50 border-blue-600 text-blue-600">
                      Auto
                    </Button>
                    <Button variant="outline" className="rounded-l-none rounded-r-none">
                      Manual
                    </Button>
                    <Button variant="outline" className="rounded-l-none">
                      Assisted
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column - Results (40%) */}
        <div className="w-full lg:w-2/5 flex flex-col gap-4">
          {/* Measurement Results */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Measurement Results</CardTitle>
              <CardDescription>Last updated: {new Date().toLocaleTimeString()}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Height</p>
                    <p className="text-2xl font-semibold">
                      {measurements.height} <span className="text-sm">cm</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Shoulder Width</p>
                    <p className="text-2xl font-semibold">
                      {measurements.shoulderWidth} <span className="text-sm">cm</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Chest</p>
                    <p className="text-2xl font-semibold">
                      {measurements.chest} <span className="text-sm">cm</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Waist</p>
                    <p className="text-2xl font-semibold">
                      {measurements.waist} <span className="text-sm">cm</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Hips</p>
                    <p className="text-2xl font-semibold">
                      {measurements.hips} <span className="text-sm">cm</span>
                    </p>
                  </div>

                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Inseam</p>
                    <p className="text-2xl font-semibold">
                      {measurements.inseam} <span className="text-sm">cm</span>
                    </p>
                  </div>
                </div>

                <div className="pt-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Body Composition Analysis</p>
                    <Badge variant="outline">AI Estimated</Badge>
                  </div>
                  <div className="mt-2 grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-blue-50 p-2">
                      <p className="text-xs text-muted-foreground">Body Type</p>
                      <p className="font-medium">Mesomorph</p>
                    </div>
                    <div className="rounded-lg bg-blue-50 p-2">
                      <p className="text-xs text-muted-foreground">BMI</p>
                      <p className="font-medium">22.4</p>
                    </div>
                    <div className="rounded-lg bg-blue-50 p-2">
                      <p className="text-xs text-muted-foreground">Body Fat %</p>
                      <p className="font-medium">~18%</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Measurement History */}
          <Card className="flex-1">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle>Measurement History</CardTitle>
                <Button variant="ghost" size="sm" className="h-8 gap-1">
                  <History className="h-4 w-4" />
                  View All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="table">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="table">Table</TabsTrigger>
                  <TabsTrigger value="chart">Chart</TabsTrigger>
                </TabsList>
                <TabsContent value="table" className="pt-4">
                  <div className="rounded-md border">
                    <div className="grid grid-cols-4 gap-2 p-3 text-sm font-medium border-b bg-muted/50">
                      <div>Date</div>
                      <div>Chest</div>
                      <div>Waist</div>
                      <div>Hips</div>
                    </div>
                    <div className="divide-y">
                      {history.map((entry, index) => (
                        <div key={index} className="grid grid-cols-4 gap-2 p-3 text-sm">
                          <div>{entry.date}</div>
                          <div>{entry.chest} cm</div>
                          <div>{entry.waist} cm</div>
                          <div>{entry.hips} cm</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </TabsContent>
                <TabsContent value="chart" className="pt-4">
                  <div className="h-[200px] flex items-center justify-center bg-muted/20 rounded-md">
                    <div className="text-center">
                      <LineChart className="h-10 w-10 mx-auto mb-2 text-muted-foreground/50" />
                      <p className="text-sm text-muted-foreground">Measurement trends will appear here</p>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* Data Export */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Export Data</CardTitle>
              <CardDescription>Download your measurement data</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="flex-1">
                  <FileText className="mr-2 h-4 w-4" />
                  PDF Report
                </Button>
                <Button variant="outline" className="flex-1">
                  <FileCsv className="mr-2 h-4 w-4" />
                  CSV
                </Button>
                <Button variant="outline" className="flex-1">
                  <FileJson className="mr-2 h-4 w-4" />
                  JSON
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="flex-1">
                      <Download className="mr-2 h-4 w-4" />
                      More Options
                      <ChevronDown className="ml-2 h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem>Excel (.xlsx)</DropdownMenuItem>
                    <DropdownMenuItem>Images (.zip)</DropdownMenuItem>
                    <DropdownMenuItem>3D Model (.obj)</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
